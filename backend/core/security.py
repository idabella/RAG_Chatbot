from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import secrets
import hashlib
import hmac
import string
import random

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings


class UserRole(str, Enum):
    """Définit les rôles des utilisateurs dans le système."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class Permission(str, Enum):
    """Définit les permissions granulaires pour les actions dans le système."""
    READ_CHAT = "read_chat"
    WRITE_CHAT = "write_chat"
    UPLOAD_DOCUMENTS = "upload_documents"
    MANAGE_DOCUMENTS = "manage_documents"
    ADMIN_PANEL = "admin_panel"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"


# Mappage centralisé des rôles à leurs permissions.
ROLE_PERMISSIONS = {
    UserRole.USER: [
        Permission.READ_CHAT,
        Permission.WRITE_CHAT,
    ],
    UserRole.MODERATOR: [
        Permission.READ_CHAT,
        Permission.WRITE_CHAT,
        Permission.UPLOAD_DOCUMENTS,
        Permission.MANAGE_DOCUMENTS,
        Permission.VIEW_ANALYTICS,
    ],
    UserRole.ADMIN: list(Permission),  # L'admin a toutes les permissions.
}


class SecurityException(HTTPException):
    """Exception personnalisée pour les erreurs de sécurité, héritant de HTTPException."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


# Contexte pour le hachage et la vérification des mots de passe.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma de sécurité pour les Bearer Tokens (JWT).
security_scheme = HTTPBearer()


class PasswordUtils:
    """Classe utilitaire pour la gestion des mots de passe."""
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe en clair par rapport à sa version hachée."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hache un mot de passe en utilisant bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Valide la robustesse d'un mot de passe."""
        min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', 8)
        if len(password) < min_length:
            return False
        
        # Vérifie la présence de majuscules, minuscules, chiffres et caractères spéciaux.
        return (
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        )

    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Génère un mot de passe aléatoire et robuste."""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(characters) for _ in range(length))
            if PasswordUtils.validate_password_strength(password):
                return password


class JWTManager:
    """
    Gère la création et la vérification des tokens JWT en utilisant PyJWT.
    """
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def _create_token(self, data: dict, expires_delta: timedelta, token_type: str) -> str:
        """Méthode interne pour créer un token JWT."""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "type": token_type,
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crée un token d'accès JWT.
        Utilise une durée par défaut si expires_delta n'est pas fourni.
        """
        if expires_delta is None:
            minutes = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)
            expires_delta = timedelta(minutes=minutes)
            
        return self._create_token(data, expires_delta, "access")

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crée un token de rafraîchissement JWT.
        Utilise une durée par défaut si expires_delta n'est pas fourni.
        """
        if expires_delta is None:
            days = getattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS', 7)
            expires_delta = timedelta(days=days)
            
        return self._create_token(data, expires_delta, "refresh")

    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """Vérifie et décode un token JWT, en gérant les erreurs."""
        credentials_exception = SecurityException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if "sub" not in payload:
                raise credentials_exception
            
            if payload.get("type") != token_type:
                raise SecurityException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise SecurityException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except PyJWTError:
            raise credentials_exception


class PermissionManager:
    """Classe utilitaire pour la gestion des permissions basées sur les rôles."""
    @staticmethod
    def get_user_permissions(user_role: UserRole) -> List[Permission]:
        """Récupère la liste des permissions pour un rôle donné."""
        return ROLE_PERMISSIONS.get(user_role, [])

    @staticmethod
    def has_permission(user_role: UserRole, permission: Permission) -> bool:
        """Vérifie si un rôle possède une permission spécifique."""
        return permission in PermissionManager.get_user_permissions(user_role)

    @staticmethod
    def require_permission(user_role: UserRole, permission: Permission):
        """Lève une exception si le rôle ne possède pas la permission requise."""
        if not PermissionManager.has_permission(user_role, permission):
            raise SecurityException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission.value}' required."
            )


# Instanciation des gestionnaires utilitaires.
password_utils = PasswordUtils()
permission_manager = PermissionManager()

# Instanciation du gestionnaire JWT.
token_manager = JWTManager(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.ALGORITHM
)

# Alias pour la rétrocompatibilité si d'autres parties du code utilisent `jwt_manager`.
jwt_manager = token_manager


def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict:
    """
    Dépendance FastAPI pour obtenir et valider le token de l'utilisateur actuel.
    À utiliser dans les routes protégées.
    """
    if not credentials:
        raise SecurityException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No credentials provided")
    
    token = credentials.credentials
    return token_manager.verify_token(token, token_type="access")


__all__ = [
    "UserRole",
    "Permission",
    "ROLE_PERMISSIONS",
    "SecurityException",
    "PasswordUtils",
    "JWTManager",
    "PermissionManager",
    "get_current_user_token",
    "password_utils",
    "token_manager",
    "jwt_manager",
    "permission_manager",
]