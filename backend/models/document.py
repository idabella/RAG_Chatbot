from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from core.database import Base


class EmbeddingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    REPROCESSING = "reprocessing"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    HTML = "html"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=True) 
    document_type = Column(Enum(DocumentType), nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    embeddings_status = Column(Enum(EmbeddingStatus), default=EmbeddingStatus.PENDING, index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    processing_attempts = Column(Integer, default=0)
    
    title = Column(String(500), nullable=True) 
    description = Column(Text, nullable=True)  
    language = Column(String(10), nullable=True)  
    tags = Column(JSON, nullable=True)  
    category = Column(String(100), nullable=True, index=True)  
    
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    
    embedding_model = Column(String(100), nullable=True)
    embedding_dimensions = Column(Integer, nullable=True)
    total_embeddings = Column(Integer, default=0)
    
    quality_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    version = Column(Integer, default=1)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    metad = Column(JSON, nullable=True)
    
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    parent_document = relationship("Document", remote_side=[id])
    child_documents = relationship("Document", back_populates="parent_document")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.embeddings_status}')>"

    @property
    def is_processed(self) -> bool:
        return self.embeddings_status == EmbeddingStatus.COMPLETED

    @property
    def is_processing(self) -> bool:
        return self.embeddings_status == EmbeddingStatus.PROCESSING

    @property
    def has_failed(self) -> bool:
        return self.embeddings_status == EmbeddingStatus.FAILED

    @property
    def processing_duration(self) -> Optional[float]:
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None

    @property
    def file_size_mb(self) -> float:
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

    def get_metad(self, key: str, default: Any = None) -> Any:
        if self.metad and isinstance(self.metad, dict):
            return self.metad.get(key, default)
        return default

    def set_metad(self, key: str, value: Any) -> None:
        if self.metad is None:
            self.metad = {}
        elif not isinstance(self.metad, dict):
            self.metad = {}
        self.metad[key] = value

    def add_tag(self, tag: str) -> None:
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def update_access_time(self) -> None:
        self.last_accessed_at = datetime.utcnow()

    def mark_as_processing(self) -> None:
        self.embeddings_status = EmbeddingStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
        self.processing_attempts += 1

    def mark_as_completed(self, chunk_count: int = 0, embedding_count: int = 0) -> None:
        self.embeddings_status = EmbeddingStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
        self.chunk_count = chunk_count
        self.total_embeddings = embedding_count
        self.processing_error = None

    def mark_as_failed(self, error_message: str) -> None:
        self.embeddings_status = EmbeddingStatus.FAILED
        self.processing_error = error_message
        self.processing_completed_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'document_type': self.document_type.value,
            'mime_type': self.mime_type,
            'embeddings_status': self.embeddings_status.value,
            'title': self.title,
            'description': self.description,
            'language': self.language,
            'tags': self.tags,
            'category': self.category,
            'word_count': self.word_count,
            'chunk_count': self.chunk_count,
            'quality_score': self.quality_score,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processing_duration': self.processing_duration
        }


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=True)
    
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(500), nullable=True)
    
    embedding_vector = Column(Text, nullable=True)
    embedding_model = Column(String(100), nullable=True)
    embedding_id = Column(String(100), nullable=True, index=True)
    
    quality_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    preprocessing_applied = Column(JSON, nullable=True)
    language = Column(String(10), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    metad = Column(JSON, nullable=True)
    
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"

    @property
    def preview(self) -> str:
        if self.content:
            return self.content[:100] + "..." if len(self.content) > 100 else self.content
        return ""

    def get_embedding_vector(self) -> Optional[List[float]]:
        if self.embedding_vector:
            try:
                return json.loads(self.embedding_vector)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def set_embedding_vector(self, vector: List[float]) -> None:
        self.embedding_vector = json.dumps(vector)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'document_id': self.document_id,
            'content': self.content,
            'chunk_index': self.chunk_index,
            'chunk_size': self.chunk_size,
            'word_count': self.word_count,
            'page_number': self.page_number,
            'section_title': self.section_title,
            'quality_score': self.quality_score,
            'language': self.language,
            'preview': self.preview,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

