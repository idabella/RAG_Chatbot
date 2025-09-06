from sqlalchemy import Column, Integer, String, DateTime, Enum  as SQLAlchemyEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from passlib.context import CryptContext
from typing import List

from core.database import Base
from models.token import RefreshToken 


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole, name="user_role_enum", create_type=False), default=UserRole.USER, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    conversations = relationship(
        "Conversation", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    messages = relationship(
        "Message", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    uploaded_documents = relationship(
        "Document",
        back_populates="uploaded_by_user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    refresh_tokens = relationship(
        "RefreshToken", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )

    def update_last_login(self):
        """Méthode pratique pour mettre à jour la date de dernière connexion."""
        self.last_login = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    def __str__(self) -> str:
        return f"{self.email} ({self.role.value})"
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    def set_password(self, password: str) -> None:
        self.password_hash = self.get_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return self.verify_password(password, self.password_hash)
    
    def update_last_login(self) -> None:
        self.last_login = datetime.utcnow()
        self.login_count += 1
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def is_moderator(self) -> bool:
        return self.role == UserRole.MODERATOR
    
    def can_manage_documents(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MODERATOR]
    
    def can_access_admin_panel(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MODERATOR]
    
    def can_view_analytics(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]
    
    @property
    def is_new_user(self) -> bool:
        if not self.created_at:
            return True
        return (datetime.utcnow() - self.created_at).days < 7
    
    def get_conversation_count(self) -> int:
        return self.conversations.count()
    
    def get_message_count(self) -> int:
        return self.messages.count()
    
    def get_recent_conversations(self, limit: int = 10) -> List:
        from .conversation import Conversation
        return (self.conversations
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
                .all())
    
    def activate(self) -> None:
        self.is_active = True
    
    def deactivate(self) -> None:
        self.is_active = False
    
    def promote_to_moderator(self) -> None:
        if self.role == UserRole.USER:
            self.role = UserRole.MODERATOR
    
    def promote_to_admin(self) -> None:
        self.role = UserRole.ADMIN
    
    def demote_to_user(self) -> None:
        if self.role in [UserRole.ADMIN, UserRole.MODERATOR]:
            self.role = UserRole.USER
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role.value,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'conversation_count': self.get_conversation_count(),
            'message_count': self.get_message_count(),
            'is_new_user': self.is_new_user
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    @classmethod
    def create_new_user(
        cls, 
        email: str, 
        password: str,
        first_name: str = None,
        last_name: str = None,
        role: UserRole = UserRole.USER,
        db_session=None
    ) -> "User":
        user = cls(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        user.set_password(password)
        
        if db_session:
            db_session.add(user)
            db_session.flush()
        
        return user

