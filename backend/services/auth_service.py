# services/auth_service.py
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy.orm import Session
from sqlalchemy import update, func, select

from models.token import RefreshToken
from models.user import User, UserRole
from core.security import PasswordUtils
from schemas.user import UserUpdate
from schemas.auth import RegisterRequest

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------
    # CRUD / lookup utilisateur
    # ---------------------------
    def create_user(self, user_data: RegisterRequest) -> User:
        """
        Crée un utilisateur et retourne l'instance persistée.
        """
        try:
            hashed_password_str = PasswordUtils.get_password_hash(user_data.password)

            user = User(
                email=user_data.email,
                password_hash=hashed_password_str,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=UserRole.USER.value if hasattr(UserRole, "USER") else UserRole.USER,
                is_active=True
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info("Created new user: %s (id=%s)", user.email, user.id)
            return user

        except Exception as e:
            self.db.rollback()
            logger.exception("Error creating user: %s", e)
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).one_or_none()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).one_or_none()

    # ---------------------------
    # Auth
    # ---------------------------
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            return None

        if not PasswordUtils.verify_password(password, user.password_hash):
            return None

        logger.info("User authenticated: %s (id=%s)", email, user.id)
        return user

    # ---------------------------
    # Last login & login_count
    # ---------------------------
    def update_last_login(self, user_id: int) -> Optional[User]:
        """
        Met à jour last_login (UTC) et incrémente login_count de +1 de façon atomique.
        Retourne l'instance User rafraîchie (ou None si utilisateur introuvable).
        Utilise UPDATE ... RETURNING pour PostgreSQL et fallback non-atomique si échoue.
        """
        now = datetime.now(timezone.utc)
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    last_login=now,
                    login_count=(func.coalesce(User.login_count, 0) + 1),
                    updated_at=now
                )
                .returning(User.id)
            )

            result = self.db.execute(stmt)
            self.db.commit()

            row = result.fetchone()
            if not row:
                return None

            # Re-fetch ORM object so it contains current values
            user = self.get_user_by_id(user_id)
            if user:
                try:
                    self.db.refresh(user)
                except Exception:
                    # silent fallback if refresh fails
                    pass
            return user

        except Exception as e:
            # rollback & fallback
            self.db.rollback()
            logger.exception("Atomic update_last_login failed for user %s, falling back: %s", user_id, e)

            try:
                user = self.get_user_by_id(user_id)
                if not user:
                    return None

                # Ensure login_count exists and increment
                if getattr(user, "login_count", None) is None:
                    user.login_count = 0
                user.login_count = (user.login_count or 0) + 1
                user.last_login = now
                user.updated_at = now

                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                return user
            except Exception as ex:
                self.db.rollback()
                logger.exception("Fallback update_last_login failed for user %s: %s", user_id, ex)
                return None
    # ---------------------------
    # Update utilisateur
    # ---------------------------
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None

            update_data = user_data.model_dump(exclude_unset=True) if hasattr(user_data, "model_dump") else user_data.dict(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)

            user.updated_at = datetime.now(timezone.utc)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info("Updated user: %s (id=%s)", user.email, user.id)
            return user

        except Exception as e:
            self.db.rollback()
            logger.exception("Error updating user %s: %s", user_id, e)
            raise

    # ---------------------------
    # Passwords
    # ---------------------------
    def change_password(self, user_id: int, new_password: str) -> bool:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            user.password_hash = PasswordUtils.get_password_hash(new_password)
            user.updated_at = datetime.now(timezone.utc)

            # revoke old refresh tokens on password change
            self.revoke_all_refresh_tokens(user_id)

            self.db.add(user)
            self.db.commit()
            logger.info("Password changed for user: %s (id=%s)", user.email, user.id)
            return True

        except Exception as e:
            self.db.rollback()
            logger.exception("Error changing password for user %s: %s", user_id, e)
            return False

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return PasswordUtils.verify_password(plain_password, hashed_password)

    # ---------------------------
    # Activation / désactivation
    # ---------------------------
    def deactivate_user(self, user_id: int) -> bool:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)

            self.revoke_all_refresh_tokens(user_id)

            self.db.add(user)
            self.db.commit()
            logger.info("Deactivated user: %s (id=%s)", user.email, user.id)
            return True

        except Exception as e:
            self.db.rollback()
            logger.exception("Error deactivating user %s: %s", user_id, e)
            return False

    def activate_user(self, user_id: int) -> bool:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            user.is_active = True
            user.updated_at = datetime.now(timezone.utc)

            self.db.add(user)
            self.db.commit()
            logger.info("Activated user: %s (id=%s)", user.email, user.id)
            return True

        except Exception as e:
            self.db.rollback()
            logger.exception("Error activating user %s: %s", user_id, e)
            return False

    # ---------------------------
    # Refresh tokens
    # ---------------------------
    def save_refresh_token(self, user_id: int, token: str, days_valid: int = 30) -> RefreshToken:
        """Sauvegarde le token de rafraîchissement et retourne l'instance."""
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
            db_token = RefreshToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at
            )
            self.db.add(db_token)
            self.db.commit()
            self.db.refresh(db_token)
            logger.info("Saved refresh token for user %s (token id=%s)", user_id, db_token.id if hasattr(db_token, "id") else "n/a")
            return db_token
        except Exception as e:
            self.db.rollback()
            logger.exception("Error saving refresh token for user %s: %s", user_id, e)
            raise

    def is_refresh_token_valid(self, user_id: int, token: str) -> bool:
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.token == token
        ).one_or_none()

        if not db_token:
            return False

        if datetime.now(timezone.utc) > db_token.expires_at:
            try:
                self.db.delete(db_token)
                self.db.commit()
            except Exception:
                self.db.rollback()
            return False

        return True

    def update_refresh_token(self, user_id: int, old_token: str, new_token: str, days_valid: int = 30) -> None:
        try:
            db_token = self.db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token == old_token
            ).one_or_none()

            if db_token:
                db_token.token = new_token
                db_token.expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
                self.db.add(db_token)
                self.db.commit()
                logger.debug("Updated refresh token for user %s", user_id)
        except Exception as e:
            self.db.rollback()
            logger.exception("Error updating refresh token for user %s: %s", user_id, e)
            raise

    def revoke_refresh_token(self, user_id: int, refresh_token: str) -> None:
        try:
            db_token = self.db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token == refresh_token
            ).one_or_none()

            if db_token:
                self.db.delete(db_token)
                self.db.commit()
                logger.debug("Revoked refresh token for user %s", user_id)
        except Exception as e:
            self.db.rollback()
            logger.exception("Error revoking refresh token for user %s: %s", user_id, e)

    def revoke_all_refresh_tokens(self, user_id: int) -> None:
        """
        Révoque tous les refresh tokens de l'utilisateur.
        Utilise delete(..., synchronize_session=False) pour performance.
        """
        try:
            self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete(synchronize_session=False)
            self.db.commit()
            logger.info("Revoked all refresh tokens for user %s", user_id)
        except Exception as e:
            self.db.rollback()
            logger.exception("Error revoking tokens for user %s: %s", user_id, e)
            raise

    def cleanup_expired_tokens(self) -> None:
        try:
            deleted = self.db.query(RefreshToken).filter(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            ).delete(synchronize_session=False)
            self.db.commit()
            if deleted:
                logger.info("Cleaned up %s expired refresh tokens", deleted)
        except Exception as e:
            self.db.rollback()
            logger.exception("Error cleaning up expired tokens: %s", e)

    # ---------------------------
    # Statistiques & recherche
    # ---------------------------
    def get_user_stats(self) -> Dict[str, Any]:
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()

        admin_users = self.db.query(User).filter(User.role == UserRole.ADMIN.value).count()
        regular_users = self.db.query(User).filter(User.role == UserRole.USER.value).count()

        recent_users = self.db.query(User).filter(
            User.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).count()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "regular_users": regular_users,
            "recent_registrations": recent_users,
            "active_sessions": self.db.query(RefreshToken).count()
        }

    def search_users(
        self,
        query: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[User]:

        db_query = self.db.query(User)

        if query:
            like = f"%{query}%"
            db_query = db_query.filter(
                (User.email.ilike(like)) |
                (User.first_name.ilike(like)) |
                (User.last_name.ilike(like))
            )

        if role is not None:
            # role peut être enum; compare à la valeur stockée
            db_query = db_query.filter(User.role == (role.value if hasattr(role, "value") else role))

        if is_active is not None:
            db_query = db_query.filter(User.is_active == is_active)

        return db_query.offset(offset).limit(limit).all()

    def promote_user_to_admin(self, user_id: int) -> bool:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            user.role = UserRole.ADMIN.value
            user.updated_at = datetime.now(timezone.utc)

            self.db.add(user)
            self.db.commit()
            logger.info("Promoted user to admin: %s (id=%s)", user.email, user.id)
            return True

        except Exception as e:
            self.db.rollback()
            logger.exception("Error promoting user %s to admin: %s", user_id, e)
            return False

    def demote_admin_to_user(self, user_id: int) -> bool:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            user.role = UserRole.USER.value
            user.updated_at = datetime.now(timezone.utc)

            self.db.add(user)
            self.db.commit()
            logger.info("Demoted admin to user: %s (id=%s)", user.email, user.id)
            return True

        except Exception as e:
            self.db.rollback()
            logger.exception("Error demoting admin %s to user: %s", user_id, e)
            return False
