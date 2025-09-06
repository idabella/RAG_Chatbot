from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from core.database import Base


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default=MessageRole.USER)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    confidence_score = Column(Float, nullable=True)
    sources = Column(JSON, nullable=True)
    metad = Column(JSON, nullable=True)
    
    is_processed = Column(Boolean, default=True, nullable=False)
    token_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"

    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.role.title()}: {content_preview}"

    @property
    def is_from_user(self) -> bool:
        return self.role == MessageRole.USER

    @property
    def is_from_assistant(self) -> bool:
        return self.role == MessageRole.ASSISTANT

    @property
    def is_system_message(self) -> bool:
        return self.role == MessageRole.SYSTEM

    @property
    def has_sources(self) -> bool:
        return bool(self.sources and len(self.sources) > 0)

    @property
    def source_count(self) -> int:
        return len(self.sources) if self.sources else 0

    def add_source(
        self,
        document_id: str,
        document_title: str,
        chunk_text: str,
        similarity_score: float,
        page_number: Optional[int] = None
    ) -> None:
        if not self.sources:
            self.sources = []
        
        source = {
            "document_id": document_id,
            "document_title": document_title,
            "chunk_text": chunk_text,
            "similarity_score": similarity_score,
            "page_number": page_number,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.sources.append(source)

    def set_metad(self, key: str, value: Any) -> None:
        if not self.metad:
            self.metad = {}
        
        self.metad[key] = value

    def get_metad(self, key: str, default: Any = None) -> Any:
        if not self.metad:
            return default
        
        return self.metad.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "content": self.content,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "confidence_score": self.confidence_score,
            "sources": self.sources,
            "metad": self.metad,
            "is_processed": self.is_processed,
            "token_count": self.token_count,
            "error_message": self.error_message,
            "source_count": self.source_count,
            "has_sources": self.has_sources
        }

    @classmethod
    def create_user_message(
        cls,
        conversation_id: int,
        user_id: int,
        content: str,
        token_count: Optional[int] = None
    ) -> "Message":
        return cls(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=MessageRole.USER,
            token_count=token_count
        )

    @classmethod
    def create_assistant_message(
        cls,
        conversation_id: int,
        user_id: int,
        content: str,
        confidence_score: Optional[float] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        token_count: Optional[int] = None,
        metad: Optional[Dict[str, Any]] = None
    ) -> "Message":
        return cls(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=MessageRole.ASSISTANT,
            confidence_score=confidence_score,
            sources=sources,
            token_count=token_count,
            metad=metad
        )

    @classmethod
    def create_system_message(
        cls,
        conversation_id: int,
        user_id: int,
        content: str,
        metad: Optional[Dict[str, Any]] = None
    ) -> "Message":
        return cls(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=MessageRole.SYSTEM,
            metad=metad
        )

