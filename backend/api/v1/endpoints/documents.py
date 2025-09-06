# backend/api/v1/endpoints/documents.py - VERSION CORRIGÉE POUR L'ENCODAGE
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
import uuid
from datetime import datetime
import logging
import chardet  # AJOUT pour détection d'encodage

from core.database import get_db
from core.config import settings
from models.user import User
from models.document import EmbeddingStatus
from schemas.document import (
    DocumentResponse, 
    DocumentListResponse,
    DocumentStatusResponse
)
from services.document_service import DocumentService
from services.embedding_service import EmbeddingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed file extensions for document upload
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}

# UTILISATEUR FICTIF POUR LES TESTS
FAKE_USER_ID = 1


def detect_and_read_text_file(file_content: bytes, filename: str) -> str:
    """
    Détecter l'encodage et lire le contenu d'un fichier texte
    """
    try:
        # Détection automatique de l'encodage
        detected = chardet.detect(file_content)
        encoding = detected.get('encoding', 'utf-8')
        confidence = detected.get('confidence', 0.0)
        
        logger.info(f"Encodage détecté pour {filename}: {encoding} (confiance: {confidence:.2f})")
        
        # Liste des encodages à essayer dans l'ordre de priorité
        encodings_to_try = []
        
        # Ajouter l'encodage détecté s'il a une bonne confiance
        if encoding and confidence > 0.7:
            encodings_to_try.append(encoding)
        
        # Encodages courants à essayer
        common_encodings = [
            'utf-8',
            'utf-8-sig',  # UTF-8 avec BOM
            'windows-1252',  # Encodage Windows courant
            'iso-8859-1',  # Latin-1
            'cp1252',  # Code page Windows
            'windows-1254',  # Encodage turc (détecté dans les logs)
            'latin1'
        ]
        
        # Ajouter les encodages courants
        for enc in common_encodings:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)
        
        # Ajouter l'encodage détecté même avec faible confiance
        if encoding and encoding not in encodings_to_try:
            encodings_to_try.append(encoding)
        
        # Essayer chaque encodage
        for enc in encodings_to_try:
            try:
                content_text = file_content.decode(enc)
                logger.info(f"Fichier {filename} décodé avec succès avec l'encodage: {enc}")
                
                # Nettoyer le contenu
                content_text = clean_text_content(content_text)
                return content_text
                
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.debug(f"Échec décodage avec {enc}: {str(e)}")
                continue
        
        # Si aucun encodage ne fonctionne, utiliser 'replace'
        logger.warning(f"Aucun encodage standard ne fonctionne pour {filename}, utilisation du mode 'replace'")
        content_text = file_content.decode('utf-8', errors='replace')
        content_text = clean_text_content(content_text)
        return content_text
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'encodage pour {filename}: {str(e)}")
        raise


def clean_text_content(content: str) -> str:
    """
    Nettoyer le contenu texte des caractères problématiques
    """
    import re
    
    # Remplacer les caractères mal encodés courants
    replacements = {
        '\x9e': 'œ',  # Caractère œ mal encodé
        '\x8e': 'Œ',  # Caractère Œ mal encodé
        '\x85': '…',  # Points de suspension
        '\x91': "'",  # Apostrophe courbe gauche
        '\x92': "'",  # Apostrophe courbe droite
        '\x93': '"',  # Guillemet courbe gauche
        '\x94': '"',  # Guillemet courbe droite
        '\x96': '–',  # Tiret en demi-cadratin
        '\x97': '—',  # Tiret cadratin
        '\xa0': ' ',  # Espace insécable
        '\ufffd': '',  # Caractère de remplacement Unicode
    }
    
    for old_char, new_char in replacements.items():
        content = content.replace(old_char, new_char)
    
    # Supprimer les caractères de contrôle non imprimables
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
    
    # Normaliser les espaces multiples
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    return content


def save_file_with_encoding_fix(file_content: bytes, file_path: Path, filename: str, file_extension: str):
    """
    Sauvegarder le fichier en corrigeant l'encodage pour les fichiers texte
    """
    try:
        if file_extension == ".txt":
            # Pour les fichiers texte, décoder et sauvegarder en UTF-8
            text_content = detect_and_read_text_file(file_content, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            logger.info(f"Fichier texte sauvegardé en UTF-8: {file_path}")
        else:
            # Pour les autres types de fichiers, sauvegarder tel quel
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"Fichier binaire sauvegardé: {file_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de {filename}: {str(e)}")
        raise


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("general"),
    tags: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db),
):
    """
    Upload and process a document for RAG - VERSION CORRIGÉE POUR L'ENCODAGE
    """
    try:
        logger.info(f"Document upload started by fake user {FAKE_USER_ID}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun fichier fourni"
            )
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de fichier non autorisé. Supportés: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Lecture du fichier
        try:
            file_content = await file.read()
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible de lire le fichier: {str(e)}"
            )
        
        # Check file size
        max_size = getattr(settings, 'MAX_FILE_SIZE', 10*1024*1024)
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fichier trop volumineux. Taille maximum: {max_size // (1024*1024)}MB"
            )
        
        # Validation du contenu pour les fichiers texte
        if file_extension == ".txt":
            try:
                # Tester la lecture avec détection d'encodage
                text_content = detect_and_read_text_file(file_content, file.filename)
                logger.info(f"Contenu texte validé: {len(text_content)} caractères")
                
                # Vérifier que le contenu n'est pas vide
                if not text_content.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Le fichier texte est vide ou ne contient que des espaces"
                    )
                    
            except Exception as e:
                logger.error(f"Erreur de validation du contenu texte pour {file.filename}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Impossible de lire le fichier texte. Problème d'encodage: {str(e)}"
                )
        
        # Sauvegarder le fichier
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_dir = Path(getattr(settings, 'UPLOAD_DIR', './uploads/data'))
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / unique_filename
        
        try:
            # CORRECTION PRINCIPALE: Utiliser la nouvelle fonction de sauvegarde
            save_file_with_encoding_fix(file_content, file_path, file.filename, file_extension)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la sauvegarde: {str(e)}"
            )
        
        # Process document
        try:
            embedding_service = EmbeddingService()
            await embedding_service.initialize()
            
            document_service = DocumentService(db, embedding_service)
            
            tags_list = [tag.strip() for tag in tags.split(",")] if tags else None
            
            result = await document_service.process_document(
                str(file_path),
                FAKE_USER_ID,
                category,
                tags_list
            )
            
            if not result.success:
                if file_path.exists():
                    os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message or "Erreur lors du traitement du document"
                )
            
            document = document_service.get_document(result.document_id, FAKE_USER_ID)
            
            await embedding_service.cleanup()
            
            logger.info(f"Document uploadé avec succès: {document.id}")
            
            return DocumentResponse(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                file_size=document.file_size,
                file_size_mb=document.file_size_mb,
                document_type=document.document_type,
                mime_type=document.mime_type,
                embeddings_status=document.embeddings_status,
                category=document.category,
                tags=document.tags or [],
                word_count=document.word_count,
                chunk_count=document.chunk_count,
                quality_score=document.quality_score,
                is_active=document.is_active,
                created_at=document.created_at,
                updated_at=document.updated_at,
                processing_duration=document.processing_duration,
                title=document.title,
                description=document.description,
                is_public=document.is_public
            )
            
        except HTTPException:
            # Nettoyer le fichier en cas d'erreur de traitement
            if file_path.exists():
                os.remove(file_path)
            raise
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du document: {e}")
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du traitement: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du téléchargement: {str(e)}"
        )


@router.get("/")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    status_filter: Optional[EmbeddingStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get list of documents - VERSION SANS AUTHENTIFICATION - CORRIGÉE
    """
    try:
        logger.info(f"Getting documents list for fake user {FAKE_USER_ID}")
        
        document_service = DocumentService(db)
        
        documents = document_service.get_documents(
            FAKE_USER_ID,
            limit,
            skip,
            status_filter
        )
        
        # Filter by search term if provided
        if search:
            documents = [
                doc for doc in documents 
                if search.lower() in doc.original_filename.lower() or 
                   (doc.category and search.lower() in doc.category.lower())
            ]
        
        # Filter by category if provided
        if category:
            documents = [doc for doc in documents if doc.category == category]
        
        total = len(documents) + skip
        
        # Convertir les documents en dictionnaires simples
        documents_list = []
        for doc in documents:
            doc_dict = {
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "title": doc.title,
                "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                "file_size_mb": round(doc.file_size / (1024 * 1024), 3) if doc.file_size else 0,
                "embeddings_status": doc.embeddings_status.value if hasattr(doc.embeddings_status, 'value') else str(doc.embeddings_status),
                "chunk_count": doc.chunk_count or 0,
                "is_active": doc.is_active if hasattr(doc, 'is_active') else True,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "category": doc.category,
                "tags": doc.tags or []
            }
            documents_list.append(doc_dict)
        
        return {
            "success": True,
            "message": f"Documents retrieved successfully",
            "data": {
                "documents": documents_list,
                "total": total,
                "skip": skip,
                "limit": limit,
                "count": len(documents_list)
            },
            "user_id": FAKE_USER_ID,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error getting documents list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Get document details - VERSION SANS AUTHENTIFICATION
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(document_id, FAKE_USER_ID)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document non trouvé"
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_size=document.file_size,
            file_size_mb=document.file_size_mb,
            document_type=document.document_type,
            mime_type=document.mime_type,
            embeddings_status=document.embeddings_status,
            category=document.category,
            tags=document.tags or [],
            word_count=document.word_count,
            chunk_count=document.chunk_count,
            quality_score=document.quality_score,
            is_active=document.is_active,
            created_at=document.created_at,
            updated_at=document.updated_at,
            processing_duration=document.processing_duration,
            title=document.title,
            description=document.description,
            is_public=document.is_public
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a document - VERSION SANS AUTHENTIFICATION
    """
    try:
        logger.info(f"Deleting document {document_id} by fake user {FAKE_USER_ID}")
        
        document_service = DocumentService(db)
        
        if not document_service.delete_document(document_id, FAKE_USER_ID):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document non trouvé"
            )
        
        logger.info(f"Document {document_id} deleted successfully")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Document supprimé avec succès"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


@router.get("/stats/overview")
async def get_documents_stats(
    db: Session = Depends(get_db),
):
    """
    Get document statistics overview - VERSION SANS AUTHENTIFICATION
    """
    try:
        logger.info(f"Getting document stats for fake user {FAKE_USER_ID}")
        
        document_service = DocumentService(db)
        stats = document_service.get_document_stats(FAKE_USER_ID)
        
        # Add additional stats for frontend
        enhanced_stats = {
            **stats,
            "upload_enabled": True,
            "supported_formats": list(ALLOWED_EXTENSIONS),
            "max_file_size_mb": getattr(settings, 'MAX_FILE_SIZE', 10*1024*1024) // (1024*1024)
        }
        
        return enhanced_stats
        
    except Exception as e:
        logger.exception(f"Error getting document stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@router.get("/test")
async def test_documents_endpoint():
    """
    Test endpoint - VERSION SANS AUTHENTIFICATION
    """
    return {
        "success": True,
        "message": "Documents service is running (NO AUTH MODE)",
        "fake_user_id": FAKE_USER_ID,
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "encoding_detection": "enhanced",
        "features": [
            "Document upload (no auth)",
            "PDF/DOCX/TXT processing",
            "Enhanced encoding detection for text files",
            "UTF-8 normalization",
            "Embedding generation", 
            "Category management",
            "Search functionality"
        ],
        "timestamp": datetime.now().isoformat()
    }