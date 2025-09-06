from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Le message ne peut pas être vide')
        return v.strip()


class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    message_id: int
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    timestamp: datetime
    processing_time: Optional[float] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    role: MessageRole = MessageRole.USER
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    content: str
    role: MessageRole
    created_at: datetime
    confidence_score: Optional[float] = None
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    token_count: Optional[int] = None
    has_sources: bool
    source_count: int

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    is_active: bool
    message_count: int
    summary: Optional[str] = None
    tags: List[str]
    duration_minutes: Optional[float] = None
    is_recent: bool

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    is_recent: bool

    class Config:
        from_attributes = True


class ChatHistoryRequest(BaseModel):
    conversation_id: int
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    include_sources: bool = False


class ChatHistoryResponse(BaseModel):
    conversation_id: int
    messages: List[MessageResponse]
    total_messages: int
    has_more: bool

    class Config:
        from_attributes = True


class ChatStreamChunk(BaseModel):
    chunk: str
    conversation_id: int
    is_complete: bool = False
    message_id: Optional[int] = None
    sources: Optional[List[Dict[str, Any]]] = None


class ChatWebSocketMessage(BaseModel):
    type: str = Field(..., pattern="^(chat_message|ping|join_room|leave_room)$")
    message: Optional[str] = None
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    timestamp: Optional[datetime] = None


class ChatWebSocketResponse(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatStatsResponse(BaseModel):
    total_conversations: int
    active_conversations: int
    total_messages: int
    messages_today: int
    average_messages_per_conversation: float
    most_active_users: List[Dict[str, Any]]
    conversation_trends: Dict[str, int]

    class Config:
        from_attributes = True

