from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import List, Optional

from core.database import Base 

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False, index=True)
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_message_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    is_active = Column(Boolean, default=True, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    
    summary = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    
    user = relationship(
        "User", 
        back_populates="conversations",
        lazy="select"
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"
    
    def __str__(self) -> str:
        return f"Conversation: {self.title} ({self.message_count} messages)"
    
    @property
    def is_recent(self) -> bool:
        if not self.updated_at:
            return False
        
        return datetime.utcnow() - self.updated_at.replace(tzinfo=None) < timedelta(hours=24)
    
    @property
    def duration_minutes(self) -> Optional[float]:
        if self.created_at and self.last_message_at:
            delta = self.last_message_at - self.created_at
            return round(delta.total_seconds() / 60, 2)
        return None
    
    def generate_title_from_first_message(self) -> str:
        if not self.messages:
            return "Nouvelle conversation"
        
        first_user_message = None
        for message in self.messages:
            if message.role == "user":
                first_user_message = message
                break
        
        if not first_user_message:
            return "Nouvelle conversation"
        
        content = first_user_message.content.strip()
        if len(content) > 50:
            content = content[:47] + "..."
        
        return content
    
    def update_message_count(self) -> None:
        self.message_count = len(self.messages)
    
    def update_last_message_timestamp(self) -> None:
        if self.messages:
            self.last_message_at = max(msg.created_at for msg in self.messages)
        else:
            self.last_message_at = None
    
    def archive(self) -> None:
        self.is_active = False
        self.updated_at = func.now()
    
    def restore(self) -> None:
        self.is_active = True
        self.updated_at = func.now()
    
    def add_tags(self, new_tags: List[str]) -> None:
        existing_tags = self.get_tags()
        all_tags = list(set(existing_tags + new_tags))
        self.tags = ",".join(all_tags)
    
    def get_tags(self) -> List[str]:
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def remove_tag(self, tag_to_remove: str) -> None:
        tags = self.get_tags()
        if tag_to_remove in tags:
            tags.remove(tag_to_remove)
            self.tags = ",".join(tags) if tags else None
    
    def get_last_messages(self, limit: int = 10) -> List:
        return sorted(self.messages, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_user_messages(self) -> List:
        return [msg for msg in self.messages if msg.role == "user"]
    
    def get_assistant_messages(self) -> List:
        return [msg for msg in self.messages if msg.role == "assistant"]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "summary": self.summary,
            "tags": self.get_tags(),
            "duration_minutes": self.duration_minutes,
            "is_recent": self.is_recent
        }
    
    @classmethod
    def create_new_conversation(
        cls, 
        user_id: int, 
        title: str = None,
        db_session=None
    ) -> "Conversation":
        conversation = cls(
            user_id=user_id,
            title=title or "Nouvelle conversation",
            is_active=True,
            message_count=0
        )
        
        if db_session:
            db_session.add(conversation)
            db_session.flush()
        
        return conversation

