from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional , Dict , Any
from datetime import datetime
from enum import Enum
import re 
from models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserProfileResponse(BaseModel):
    """Reponse du profil utilisateur"""
    id: int = Field(..., description="ID unique de l'utilisateur")
    email: EmailStr = Field(..., description="Adresse email")
    first_name: Optional[str] = Field(None, description="Prenom", max_length=50)
    last_name: Optional[str] = Field(None, description="Nom de famille", max_length=50)
    role: str = Field(..., description="Rôle de l'utilisateur")
    is_active: bool = Field(True, description="Compte actif")
    created_at: datetime = Field(..., description="Date de creation du compte")
    updated_at: datetime = Field(..., description="Dernière mise à jour du profil")
    last_login: Optional[datetime] = Field(None, description="Dernière connexion")
    profile_picture: Optional[str] = Field(None, description="URL de la photo de profil")
    bio: Optional[str] = Field(None, description="Biographie", max_length=500)
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Preferences utilisateur")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['user', 'admin', 'moderator', 'premium']
        if v not in valid_roles:
            raise ValueError(f'Rôle doit être un de: {valid_roles}')
        return v
    
    @validator('profile_picture')
    def validate_profile_picture(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError('URL de photo de profil invalide')
        return v
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class LoginResponse(BaseModel):
    message: str
    user: dict
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère special')
        
        return v


class RegisterResponse(BaseModel):
    message: str
    user: dict
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère special')
        
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Requête de changement de mot de passe"""
    current_password: str = Field(..., description="Mot de passe actuel")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Nouveau mot de passe (min 8 caractères)"
    )
    confirm_password: str = Field(..., description="Confirmation du nouveau mot de passe")

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Valider la force du mot de passe"""
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        
        if len(v) > 128:
            raise ValueError('Le mot de passe ne peut pas depasser 128 caractères')
        
        # Verifier la presence d'au moins une lettre minuscule
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une lettre minuscule')
        
        # Verifier la presence d'au moins une lettre majuscule
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une lettre majuscule')
        
        # Verifier la presence d'au moins un chiffre
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        
        # Verifier la presence d'au moins un caractère special
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère special')
        
        # Verifier qu'il n'y a pas d'espaces
        if ' ' in v:
            raise ValueError('Le mot de passe ne doit pas contenir d\'espaces')
        
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Verifier que les mots de passe correspondent"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v

    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldPassword123!",
                "new_password": "newSecurePassword456!",
                "confirm_password": "newSecurePassword456!"
            }
        }

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère special')
        
        return v


class TokenVerifyResponse(BaseModel):
    message: str
    user_id: int
    email: str
    role: UserRole
    is_valid: bool


class UserAuthResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthStatsResponse(BaseModel):
    total_users: int
    active_sessions: int
    login_attempts_today: int
    successful_logins_today: int
    failed_logins_today: int
    new_registrations_today: int

    class Config:
        from_attributes = True

