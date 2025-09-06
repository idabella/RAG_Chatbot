from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    HTML = "html"


class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REPROCESSING = "reprocessing"

    
class DocumentStatusResponse(BaseModel):
    """Reponse du statut d'un document"""
    document_id: int = Field(..., description="ID unique du document")
    status: EmbeddingStatus = Field(..., description="Statut d'embedding du document")
    processed_at: Optional[datetime] = Field(None, description="Date de traitement")
    error_message: Optional[str] = Field(None, description="Message d'erreur si applicable")
    chunks_count: int = Field(0, description="Nombre de chunks crees")
    progress_percentage: int = Field(0, description="Pourcentage de progression", ge=0, le=100)
    
    @validator('progress_percentage')
    def validate_progress(cls, v, values):
        # Ajuster automatiquement le pourcentage selon le statut
        if 'status' in values:
            status = values['status']
            if status == EmbeddingStatus.COMPLETED:
                return 100
            elif status == EmbeddingStatus.FAILED or status == EmbeddingStatus.CANCELLED:
                return 0
            elif status == EmbeddingStatus.PENDING or status == EmbeddingStatus.QUEUED:
                return 0
        return v
    
    class Config:
        from_attributes = True




class DocumentBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_size_mb: float
    document_type: DocumentType
    embeddings_status: EmbeddingStatus
    message: str

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_size_mb: float
    document_type: DocumentType
    mime_type: str
    embeddings_status: EmbeddingStatus
    word_count: Optional[int] = None
    chunk_count: int
    quality_score: Optional[float] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    processing_duration: Optional[float] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    id: int
    filename: str
    title: Optional[str] = None
    document_type: DocumentType
    file_size_mb: float
    embeddings_status: EmbeddingStatus
    chunk_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    content: str
    chunk_index: int
    chunk_size: int
    word_count: Optional[int] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    quality_score: Optional[float] = None
    language: Optional[str] = None
    preview: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    document_types: Optional[List[DocumentType]] = None
    categories: Optional[List[str]] = None


class DocumentSearchResult(BaseModel):
    document_id: int
    document_title: str
    chunk_text: str
    similarity_score: float
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class DocumentSearchResponse(BaseModel):
    query: str
    results: List[DocumentSearchResult]
    total_results: int
    processing_time: float


class DocumentProcessingStatus(BaseModel):
    document_id: int
    status: EmbeddingStatus
    progress_percentage: Optional[float] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    processing_attempts: int
    chunk_count: int
    total_embeddings: int

    class Config:
        from_attributes = True


class DocumentStatsResponse(BaseModel):
    total_documents: int
    active_documents: int
    processed_documents: int
    pending_documents: int
    failed_documents: int
    total_chunks: int
    documents_by_type: Dict[str, int]
    documents_by_status: Dict[str, int]
    average_processing_time: Optional[float] = None

    class Config:
        from_attributes = True

