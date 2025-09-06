# backend/api/v1/endpoints/auth.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

from core.database import get_db
from core.config import settings 
from core.security import jwt_manager 
from api.deps import get_current_user, get_rate_limiter
from models.user import User
from schemas.auth import (
    LoginRequest,
    LoginResponse, 
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    UserProfileResponse
)
from schemas.user import UserResponse
from services.auth_service import AuthService

import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
    _: None = Depends(get_rate_limiter(100, 60))
):
    """
    Register a new user and return authentication tokens.
    Frontend Integration: Creates user account and provides immediate login tokens.
    """
    try:
        auth_service = AuthService(db)

        # Check if user already exists
        existing_user = auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un utilisateur avec cet email existe déjà"
            )

        # Create new user
        user = auth_service.create_user(user_data)

        # Generate tokens
        token_payload = {
            "sub": str(user.id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }

        access_token = jwt_manager.create_access_token(
            data=token_payload,
            expires_delta=timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        )

        refresh_token = jwt_manager.create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
        )

        # Save refresh token
        auth_service.save_refresh_token(user.id, refresh_token)

        # Build user response
        now = datetime.now(timezone.utc)
        created_at = getattr(user, "created_at", None)
        if created_at is None:
            created_at_aware = now
        else:
            if getattr(created_at, "tzinfo", None) is None:
                created_at_aware = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at_aware = created_at

        user_response = UserResponse(
            id=user.id,
            email=getattr(user, "email", None),
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            role=getattr(user, "role", None),
            is_active=getattr(user, "is_active", True),
            full_name=f"{getattr(user,'first_name','') or ''} {getattr(user,'last_name','') or ''}".strip() or getattr(user, "email", ""),
            created_at=getattr(user, "created_at", None),
            updated_at=getattr(user, "updated_at", None),
            last_login=getattr(user, "last_login", None),
            login_count=getattr(user, "login_count", 0) or 0,
            conversation_count=getattr(user, "conversation_count", 0) or 0,
            message_count=getattr(user, "message_count", 0) or 0,
            is_new_user=(now - created_at_aware) < timedelta(days=7)
        )

        return RegisterResponse(
            message="Utilisateur créé avec succès",
            user=user_response.model_dump(),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur lors de l'inscription: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return tokens.
    Frontend Integration: Primary login endpoint for user authentication.
    """
    logger.info("Tentative de connexion pour %s", getattr(login_data, "email", "<unknown>"))
    try:
        auth_service = AuthService(db)

        # Authenticate user
        user = auth_service.authenticate_user(login_data.email, login_data.password)
        if not user:
            logger.warning("Échec d'authentification pour %s", login_data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Email ou mot de passe incorrect"
            )

        if not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Le compte est désactivé."
            )

        # Generate tokens
        token_payload = {
            "sub": str(user.id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }

        access_token = jwt_manager.create_access_token(
            data=token_payload, 
            expires_delta=timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        )
        refresh_token = jwt_manager.create_refresh_token(
            data={"sub": str(user.id)}, 
            expires_delta=timedelta(days=getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
        )

        # Save refresh token
        auth_service.save_refresh_token(user.id, refresh_token)

        # Update last login
        updated_user = auth_service.update_last_login(user.id)
        if updated_user:
            user = updated_user
        else:
            try:
                db_user = auth_service.get_user_by_id(user.id)
                if db_user:
                    user = db_user
            except Exception:
                logger.debug("Impossible de recharger l'utilisateur après update_last_login.")

        # Build user response
        now = datetime.now(timezone.utc)
        created_at = getattr(user, "created_at", None)
        if created_at is None:
            created_at_aware = now
        else:
            created_at_aware = created_at if getattr(created_at, "tzinfo", None) else created_at.replace(tzinfo=timezone.utc)

        user_response = UserResponse(
            id=user.id,
            email=getattr(user, "email", None),
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            role=getattr(user, "role", None),
            is_active=getattr(user, "is_active", True),
            full_name=f"{getattr(user,'first_name','') or ''} {getattr(user,'last_name','') or ''}".strip() or getattr(user, "email", ""),
            created_at=getattr(user, "created_at", None),
            updated_at=getattr(user, "updated_at", None),
            last_login=getattr(user, "last_login", None),
            login_count=getattr(user, "login_count", 0) or 0,
            conversation_count=getattr(user, "conversation_count", 0) or 0,
            message_count=getattr(user, "message_count", 0) or 0,
            is_new_user=(now - created_at_aware) < timedelta(days=7)
        )

        response = LoginResponse(
            message="Connexion réussie",
            user=user_response.model_dump(),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30) * 60)
        )
        logger.info("Connexion réussie pour %s", user.email)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur inattendue lors de la connexion pour %s: %s", getattr(login_data, "email", "<unknown>"), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur interne du serveur lors de la connexion."
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    Frontend Integration: Used by frontend to automatically refresh expired tokens.
    """
    try:
        payload = jwt_manager.verify_token(refresh_data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token de rafraîchissement invalide", 
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id = int(payload.get("sub"))
        auth_service = AuthService(db)

        if not auth_service.is_refresh_token_valid(user_id, refresh_data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token de rafraîchissement invalide ou expiré", 
                headers={"WWW-Authenticate": "Bearer"}
            )

        user = auth_service.get_user_by_id(user_id)
        if not user or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Utilisateur invalide", 
                headers={"WWW-Authenticate": "Bearer"}
            )

        token_payload = {
            "sub": str(user.id), 
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }

        new_access_token = jwt_manager.create_access_token(
            data=token_payload, 
            expires_delta=timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        )
        new_refresh_token = jwt_manager.create_refresh_token(
            data={"sub": str(user.id)}, 
            expires_delta=timedelta(days=getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
        )

        auth_service.update_refresh_token(user_id, refresh_data.refresh_token, new_refresh_token)

        return RefreshTokenResponse(
            access_token=new_access_token, 
            refresh_token=new_refresh_token, 
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur lors du rafraîchissement du token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors du rafraîchissement du token: {str(e)}"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user and revoke refresh tokens.
    Frontend Integration: Called when user explicitly logs out.
    """
    try:
        auth_service = AuthService(db)
        auth_service.revoke_all_refresh_tokens(current_user.id)
        return {"message": "Déconnexion réussie"}
    except Exception as e:
        logger.exception("Erreur lors de la déconnexion: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la déconnexion: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change user password.
    Frontend Integration: Password change functionality.
    """
    try:
        auth_service = AuthService(db)

        if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Mot de passe actuel incorrect"
            )

        if not auth_service.change_password(current_user.id, password_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Erreur lors du changement de mot de passe"
            )

        return {"message": "Mot de passe modifié avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur lors du changement de mot de passe: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors du changement de mot de passe: {str(e)}"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    Frontend Integration: Used to display user information in the frontend.
    """
    return UserProfileResponse(
        id=getattr(current_user, "id", None),
        email=getattr(current_user, "email", None),
        first_name=getattr(current_user, "first_name", None),
        last_name=getattr(current_user, "last_name", None),
        role=getattr(current_user, "role", None),
        is_active=getattr(current_user, "is_active", True),
        created_at=getattr(current_user, "created_at", None),
        updated_at=getattr(current_user, "updated_at", None),
        last_login=getattr(current_user, "last_login", None),
        profile_picture=getattr(current_user, "profile_picture", None),
        bio=getattr(current_user, "bio", None),
        preferences=getattr(current_user, "preferences", {}) or {}
    )


@router.get("/verify-token")
async def verify_token_endpoint(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if current token is valid.
    Frontend Integration: Used by frontend to check authentication status.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }


# Additional endpoint for frontend connection testing
@router.get("/test")
async def test_auth_endpoint():
    """
    Test endpoint for frontend-backend connection.
    Frontend Integration: Used to verify API connectivity.
    """
    return {
        "success": True,
        "message": "Auth service is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }