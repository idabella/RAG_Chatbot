from pydantic import BaseModel, EmailStr, Field, field_validator, computed_field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum 

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password', mode='after')
    @classmethod
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


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password', mode='after')
    @classmethod
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


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0

    @computed_field
    def full_name(self) -> str:
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or self.email

    @computed_field
    def conversation_count(self) -> int:
        return 0  # Compute in endpoint if relationships exist

    @computed_field
    def message_count(self) -> int:
        return 0  # Compute in endpoint if relationships exist

    @computed_field
    def is_new_user(self) -> bool:
        now = datetime.now(timezone.utc)
        created_at_aware = self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)
        return (now - created_at_aware) < timedelta(days=7)

    model_config = {'from_attributes': True}


class UserListResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    conversation_count: int = 0

    model_config = {'from_attributes': True}


class UserProfileResponse(UserResponse):
    pass


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    new_users_this_week: int
    users_by_role: dict
    recent_registrations: List[UserListResponse]

    model_config = {'from_attributes': True}