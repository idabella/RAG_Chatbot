from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging
import html
import re
from datetime import datetime

# SUPPRESSION DES IMPORTS D'AUTHENTIFICATION POUR LES TESTS
from core.database import get_db
from models.user import User, UserRole
from schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    MessageResponse, 
    ConversationResponse,
    ConversationCreate,
    ConversationListResponse,
    ChatHistoryResponse
)
from services.chat_service import ChatService
from services.rag_service import RAGService
from services.embedding_service import EmbeddingService

router = APIRouter()
logger = logging.getLogger(__name__)

# UTILISATEUR FICTIF POUR LES TESTS
FAKE_USER_ID = 1


def get_or_create_fake_user(db: Session) -> User:
    """Créer ou récupérer l'utilisateur fictif pour les tests"""
    fake_user = db.query(User).filter(User.id == FAKE_USER_ID).first()
    
    if not fake_user:
        from core.security import get_password_hash
        
        fake_user = User(
            email="fake@test.com",
            username="fake_user",
            hashed_password=get_password_hash("fake123"),
            is_active=True,
            is_admin=True
        )
        db.add(fake_user)
        db.commit()
        db.refresh(fake_user)
        logger.info(f"Utilisateur fictif créé avec ID: {fake_user.id}")
    
    return fake_user


class ResponseFormatter:
    """Classe pour formater les réponses de manière cohérente"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Nettoyer le texte de base"""
        if not text:
            return ""
        
        # Supprimer les caractères problématiques
        text = text.replace('µ', '').strip()
        
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s+', '\n', text)
        
        # Normaliser les sauts de ligne
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def format_markdown(text: str) -> str:
        """Améliorer le formatage Markdown"""
        if not text:
            return ""
        
        # Nettoyer d'abord
        text = ResponseFormatter.clean_text(text)
        
        # Améliorer les listes
        text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\*\s+', '• ', text, flags=re.MULTILINE)
        
        # Améliorer les titres
        text = re.sub(r'^#{1}\s+(.+)', r'# \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{2}\s+(.+)', r'## \1', text, flags=re.MULTILINE)
        text = re.sub(r'^#{3}\s+(.+)', r'### \1', text, flags=re.MULTILINE)
        
        # Assurer les espaces autour du gras/italique
        text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
        text = re.sub(r'\*([^*]+)\*', r'*\1*', text)
        
        # Améliorer les paragraphes
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Si c'est une liste, améliorer le formatage
                if paragraph.startswith('•'):
                    items = paragraph.split('\n')
                    formatted_items = []
                    for item in items:
                        item = item.strip()
                        if item and not item.startswith('•'):
                            item = '• ' + item
                        if item:
                            formatted_items.append(item)
                    paragraph = '\n'.join(formatted_items)
                
                formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)
    
    @staticmethod
    def extract_key_info(text: str) -> Dict[str, Any]:
        """Extraire les informations clés du texte"""
        key_info = {
            'has_phone_numbers': bool(re.search(r'0[567]\d{8}|\+212\d{9}', text)),
            'has_amounts': bool(re.search(r'\d+[,.]?\d*\s*(?:DH|MAD|€)', text)),
            'has_references': bool(re.search(r'[A-Z]-\d{4}-\d{7}', text)),
            'has_dates': bool(re.search(r'\d{1,2}/\d{1,2}/\d{4}', text)),
            'word_count': len(text.split()) if text else 0,
            'char_count': len(text) if text else 0,
            'line_count': len(text.split('\n')) if text else 0
        }
        
        # Extraire les entités spécifiques
        phone_numbers = re.findall(r'0[567]\d{8}|\+212\d{9}', text)
        amounts = re.findall(r'\d+[,.]?\d*\s*(?:DH|MAD|€)', text)
        references = re.findall(r'[A-Z]-\d{4}-\d{7}', text)
        
        if phone_numbers:
            key_info['phone_numbers'] = phone_numbers
        if amounts:
            key_info['amounts'] = amounts
        if references:
            key_info['references'] = references
            
        return key_info
    
    @staticmethod
    def format_response_content(content: str) -> Dict[str, Any]:
        """Formater complètement le contenu de la réponse"""
        if not content:
            return {
                'formatted_content': '',
                'original_content': content,
                'key_info': {},
                'formatting_applied': []
            }
        
        formatting_steps = []
        original_content = content
        
        # 1. Nettoyage de base
        content = ResponseFormatter.clean_text(content)
        if content != original_content:
            formatting_steps.append('text_cleaning')
        
        # 2. Formatage Markdown
        formatted_content = ResponseFormatter.format_markdown(content)
        if formatted_content != content:
            formatting_steps.append('markdown_formatting')
        
        # 3. Extraction des informations clés
        key_info = ResponseFormatter.extract_key_info(formatted_content)
        
        return {
            'formatted_content': formatted_content,
            'original_content': original_content,
            'key_info': key_info,
            'formatting_applied': formatting_steps,
            'content_type': 'markdown',
            'encoding': 'utf-8'
        }


def create_chat_response(
    message: str,
    conversation_id: int,
    message_id: int = None,
    sources: List[Dict] = None,
    confidence: float = 0.0,
    processing_time: float = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Créer une réponse de chat bien formatée"""
    
    # Formater le contenu principal
    formatted_data = ResponseFormatter.format_response_content(message)
    
    response_data = {
        "message": formatted_data['formatted_content'],
        "conversation_id": conversation_id,
        "message_id": message_id,
        "sources": sources or [],
        "confidence": confidence,
        "timestamp": datetime.now().isoformat(),
        "processing_time": processing_time,
        "formatting": {
            "original_length": len(formatted_data['original_content']),
            "formatted_length": len(formatted_data['formatted_content']),
            "steps_applied": formatted_data['formatting_applied'],
            "content_type": formatted_data['content_type'],
            "encoding": formatted_data['encoding'],
            "key_info": formatted_data['key_info']
        },
        "metadata": metadata or {},
        "response_quality": {
            "has_specific_data": any([
                formatted_data['key_info'].get('has_phone_numbers', False),
                formatted_data['key_info'].get('has_amounts', False),
                formatted_data['key_info'].get('has_references', False)
            ]),
            "response_length": "short" if len(message.split()) < 20 else "medium" if len(message.split()) < 100 else "long",
            "confidence_level": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
        }
    }
    
    return response_data


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Send a message and get AI response - VERSION AMÉLIORÉE AVEC FORMATAGE AVANCÉ
    """
    embedding_service = None
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing message for fake user {FAKE_USER_ID}: '{chat_request.message[:50]}...'")
        
        # Utiliser l'utilisateur fictif
        current_user = get_or_create_fake_user(db)
        
        # Initialiser les services
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        rag_service = RAGService(embedding_service)
        await rag_service.initialize()
        
        chat_service = ChatService(db, rag_service)
        
        # Traiter le message
        response = await chat_service.process_message(current_user.id, chat_request)
        
        # Calculer le temps de traitement
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Créer la réponse formatée
        formatted_response = create_chat_response(
            message=response.message,
            conversation_id=response.conversation_id,
            message_id=response.message_id,
            sources=response.sources,
            confidence=response.confidence,
            processing_time=processing_time,
            metadata={
                "user_id": current_user.id,
                "request_timestamp": start_time.isoformat(),
                "model_used": "RAG with improved formatting",
                "query_length": len(chat_request.message),
                "query_type": "standard"
            }
        )
        
        logger.info(f"Message processed successfully for user {current_user.id} in {processing_time:.2f}s")
        
        return JSONResponse(
            content=jsonable_encoder(formatted_response),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Response-Quality": formatted_response["response_quality"]["confidence_level"],
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.exception(f"Error processing message: {e}")
        
        error_response = {
            "error": True,
            "message": "Je rencontre des difficultés techniques pour traiter votre demande. Veuillez réessayer.",
            "conversation_id": getattr(chat_request, 'conversation_id', None),
            "details": str(e) if logger.isEnabledFor(logging.DEBUG) else "Erreur technique",
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time,
            "formatting": {
                "content_type": "error",
                "encoding": "utf-8",
                "steps_applied": ["error_formatting"]
            },
            "metadata": {
                "error_type": type(e).__name__,
                "recovery_suggestions": [
                    "Vérifiez votre connexion",
                    "Reformulez votre question",
                    "Contactez le support si le problème persiste"
                ]
            }
        }
        
        return JSONResponse(
            content=jsonable_encoder(error_response),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json; charset=utf-8"
        )
    finally:
        # Nettoyage des services
        if embedding_service:
            try:
                await embedding_service.cleanup()
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")


@router.post("/message/stream")
async def send_message_stream(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Send a message and get streaming AI response - VERSION AMÉLIORÉE
    """
    async def generate_response():
        embedding_service = None
        start_time = datetime.now()
        accumulated_content = ""
        
        try:
            logger.info(f"Processing streaming message for fake user {FAKE_USER_ID}")
            
            current_user = get_or_create_fake_user(db)
            
            # Envoyer les métadonnées initiales
            init_data = {
                'type': 'init',
                'conversation_id': getattr(chat_request, 'conversation_id', None),
                'user_id': current_user.id,
                'timestamp': datetime.now().isoformat(),
                'encoding': 'utf-8'
            }
            yield f"data: {json.dumps(init_data, ensure_ascii=False)}\n\n"
            
            embedding_service = EmbeddingService()
            await embedding_service.initialize()
            
            rag_service = RAGService(embedding_service)
            await rag_service.initialize()
            
            chat_service = ChatService(db, rag_service)
            
            conversation = chat_service.get_or_create_conversation(
                current_user.id, 
                chat_request.conversation_id
            )
            
            user_message = chat_service.create_message(
                conversation.id,
                current_user.id,
                chat_request.message,
                "user"
            )
            
            history = chat_service.get_conversation_history(conversation.id)
            
            # Stream la réponse avec formatage en temps réel
            chunk_count = 0
            async for chunk in rag_service.generate_response_stream(
                query=chat_request.message,
                user_id=current_user.id,
                conversation_id=conversation.id,
                conversation_history=history
            ):
                if "content" in chunk:
                    raw_chunk = chunk["content"]
                    accumulated_content += raw_chunk
                    
                    # Appliquer un formatage léger en temps réel
                    clean_chunk = ResponseFormatter.clean_text(raw_chunk)
                    
                    chunk_data = {
                        'type': 'content',
                        'chunk': clean_chunk,
                        'chunk_index': chunk_count,
                        'conversation_id': conversation.id,
                        'accumulated_length': len(accumulated_content),
                        'timestamp': datetime.now().isoformat(),
                        'encoding': 'utf-8'
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    chunk_count += 1
                    
                elif "metadata" in chunk:
                    metadata_data = {
                        'type': 'metadata',
                        'sources': chunk.get('sources', []),
                        'confidence': chunk.get('confidence', 0.0),
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(metadata_data, ensure_ascii=False)}\n\n"
                    
                elif "error" in chunk:
                    error_data = {
                        'type': 'error',
                        'error': chunk['error'],
                        'timestamp': datetime.now().isoformat(),
                        'encoding': 'utf-8'
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    break
            
            # Formatage final complet
            final_formatted = ResponseFormatter.format_response_content(accumulated_content)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Sauvegarder le message formaté
            assistant_message = chat_service.create_message(
                conversation.id,
                current_user.id,
                final_formatted['formatted_content'],
                "assistant"
            )
            
            # Envoyer les données finales
            final_data = {
                'type': 'complete',
                'message_id': assistant_message.id,
                'final_content': final_formatted['formatted_content'],
                'processing_time': processing_time,
                'total_chunks': chunk_count,
                'formatting_info': {
                    'steps_applied': final_formatted['formatting_applied'],
                    'key_info': final_formatted['key_info'],
                    'original_length': len(accumulated_content),
                    'formatted_length': len(final_formatted['formatted_content'])
                },
                'timestamp': datetime.now().isoformat(),
                'encoding': 'utf-8'
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.exception(f"Error in streaming response: {e}")
            
            error_data = {
                'type': 'error',
                'error': f'Erreur lors du traitement: {str(e)}',
                'processing_time': processing_time,
                'recovery_suggestions': [
                    'Réessayez votre requête',
                    'Vérifiez votre connexion',
                    'Reformulez votre question'
                ],
                'timestamp': datetime.now().isoformat(),
                'encoding': 'utf-8'
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            
        finally:
            if embedding_service:
                try:
                    await embedding_service.cleanup()
                except Exception as e:
                    logger.warning(f"Error during cleanup: {e}")
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "X-Stream-Format": "enhanced-formatting"
        }
    )


@router.get("/test")
async def test_chat_endpoint():
    """Test endpoint avec formatage avancé"""
    test_message = """
    # Test de Formatage Avancé
    
    Voici un exemple de **réponse formatée** avec différents éléments :
    
    ## Informations de test
    - Numéro de téléphone : 0657794462
    - Montant : 56,99 DH
    - Référence : F-0825-0986083
    - Date : 29/08/2025
    
    ### Caractéristiques
    * Formatage *markdown* amélioré
    * Nettoyage automatique des caractères µ problématiques
    * Gestion correcte des **datetime**
    * Extraction d'entités spécifiques
    
    Ce texte contient des éléments spéciaux pour tester le formatage.
    """
    
    # Appliquer le formatage
    formatted_data = ResponseFormatter.format_response_content(test_message)
    
    test_response = {
        "success": True,
        "service_status": "Chat service running with enhanced formatting",
        "fake_user_id": FAKE_USER_ID,
        "current_timestamp": datetime.now().isoformat(),
        "test_formatting": {
            "original_content": test_message,
            "formatted_content": formatted_data['formatted_content'],
            "key_info_extracted": formatted_data['key_info'],
            "formatting_steps": formatted_data['formatting_applied'],
            "content_analysis": {
                "has_phone": formatted_data['key_info'].get('has_phone_numbers', False),
                "has_amounts": formatted_data['key_info'].get('has_amounts', False),
                "has_references": formatted_data['key_info'].get('has_references', False),
                "word_count": formatted_data['key_info'].get('word_count', 0)
            }
        },
        "features": [
            "Advanced text formatting",
            "Markdown improvement", 
            "Entity extraction",
            "Real-time streaming with formatting",
            "Error handling with recovery suggestions",
            "Performance monitoring",
            "UTF-8 encoding support",
            "Datetime serialization"
        ],
        "formatting": {
            "content_type": "json",
            "encoding": "utf-8",
            "processed": True,
            "version": "2.0"
        }
    }
    
    return JSONResponse(
        content=jsonable_encoder(test_response),
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Formatting-Version": "2.0",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.post("/test/format")
async def test_format_content(request: Dict[str, Any]):
    """Endpoint pour tester le formatage d'un contenu spécifique"""
    try:
        content = request.get("content", "")
        
        if not content:
            return JSONResponse(
                content={"error": "Content is required"},
                status_code=400
            )
        
        # Appliquer le formatage complet
        result = ResponseFormatter.format_response_content(content)
        
        # Ajouter des statistiques de comparaison
        comparison = {
            "length_difference": len(result['formatted_content']) - len(result['original_content']),
            "formatting_improvement": len(result['formatting_applied']) > 0,
            "entities_found": sum([
                result['key_info'].get('has_phone_numbers', False),
                result['key_info'].get('has_amounts', False),
                result['key_info'].get('has_references', False),
                result['key_info'].get('has_dates', False)
            ]),
            "quality_score": min(1.0, (
                len(result['formatting_applied']) * 0.2 + 
                result['key_info'].get('word_count', 0) * 0.01 +
                sum([
                    result['key_info'].get('has_phone_numbers', False),
                    result['key_info'].get('has_amounts', False),
                    result['key_info'].get('has_references', False)
                ]) * 0.3
            ))
        }
        
        response_data = {
            "original": result['original_content'],
            "formatted": result['formatted_content'],
            "key_info": result['key_info'],
            "formatting_applied": result['formatting_applied'],
            "comparison": comparison,
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(
            content=jsonable_encoder(response_data),
            media_type="application/json; charset=utf-8"
        )
        
    except Exception as e:
        return JSONResponse(
            content=jsonable_encoder({"error": str(e)}),
            status_code=500
        )


# Les autres endpoints restent inchangés mais peuvent utiliser ResponseFormatter si besoin
@router.get("/history/{conversation_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get chat history avec formatage amélioré"""
    try:
        current_user = get_or_create_fake_user(db)
        
        chat_service = ChatService(db)
        
        conversation = chat_service.get_conversation(conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation non trouvée"
            )
        
        messages = chat_service.get_messages(conversation_id, limit, offset)
        total_messages = chat_service.get_message_count(conversation_id)
        
        message_responses = []
        for msg in messages:
            # Appliquer le formatage avancé aux messages historiques
            formatted_data = ResponseFormatter.format_response_content(msg.content)
            
            message_responses.append(MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                user_id=msg.user_id,
                content=formatted_data['formatted_content'],
                role=msg.role,
                created_at=msg.created_at,
                confidence_score=getattr(msg, 'confidence_score', 0.0),
                sources=getattr(msg, 'sources', []),
                metadata={
                    **getattr(msg, 'metadata', {}),
                    'formatting_info': {
                        'steps_applied': formatted_data['formatting_applied'],
                        'key_info': formatted_data['key_info']
                    }
                },
                token_count=getattr(msg, 'token_count', 0),
                has_sources=getattr(msg, 'has_sources', False),
                source_count=getattr(msg, 'source_count', 0)
            ))
        
        response_data = ChatHistoryResponse(
            conversation_id=conversation_id,
            messages=message_responses,
            total_messages=total_messages,
            has_more=offset + limit < total_messages
        )
        
        return JSONResponse(
            content=jsonable_encoder(response_data.dict()),
            media_type="application/json; charset=utf-8"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )