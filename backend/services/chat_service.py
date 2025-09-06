import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.conversation import Conversation
from models.message import Message
from schemas.chat import ChatRequest, ChatResponse, MessageResponse
from services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatService:
    """Service de gestion des conversations et messages de chat"""
    
    def __init__(self, db: Session, rag_service: Optional[RAGService] = None):
        self.db = db
        self.rag_service = rag_service
    
    async def process_message(self, user_id: int, chat_request: ChatRequest) -> ChatResponse:
        """Traiter un message de chat et générer une réponse"""
        try:
            # Créer ou récupérer la conversation
            conversation = self.get_or_create_conversation(user_id, chat_request.conversation_id)
            
            # Créer le message utilisateur
            user_message = self.create_message(
                conversation.id,
                user_id,
                chat_request.message,
                "user"
            )
            
            # Générer la réponse avec RAG si disponible
            if self.rag_service:
                # Récupérer l'historique de conversation
                history = self.get_conversation_history(conversation.id)
                
                # Générer la réponse
                rag_response = await self.rag_service.generate_response(
                    query=chat_request.message,
                    conversation_history=history,
                    user_id=user_id,
                    conversation_id=conversation.id
                )
                
                response_text = rag_response.get("response", "Je ne peux pas répondre pour le moment.")
                sources = rag_response.get("sources", [])
                confidence = rag_response.get("confidence", 0.0)
            else:
                response_text = "Service de réponse non disponible."
                sources = []
                confidence = 0.0
            
            # Créer le message assistant
            assistant_message = self.create_message(
                conversation.id,
                user_id,
                response_text,
                "assistant"
            )
            
            return ChatResponse(
                message=response_text,
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                sources=sources,
                confidence=confidence,
                timestamp=assistant_message.created_at
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            raise
    
    def get_or_create_conversation(self, user_id: int, conversation_id: Optional[int] = None) -> Conversation:
        """Récupérer ou créer une conversation"""
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            
            if conversation:
                return conversation
        
        # Créer une nouvelle conversation
        conversation = Conversation(
            user_id=user_id,
            title="Nouvelle conversation",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def create_conversation(self, user_id: int, title: str) -> Conversation:
        """Créer une nouvelle conversation avec un titre spécifique"""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def create_message(self, conversation_id: int, user_id: int, content: str, role: str) -> Message:
        """Créer un nouveau message"""
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=role,
            created_at=datetime.now()
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_conversation(self, conversation_id: int, user_id: int) -> Optional[Conversation]:
        """Récupérer une conversation spécifique"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
    
    def get_conversation_history(self, conversation_id: int) -> List[Dict[str, str]]:
        """Récupérer l'historique d'une conversation"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    
    def get_messages(self, conversation_id: int, limit: int = 50, offset: int = 0) -> List[Message]:
        """Récupérer les messages d'une conversation avec pagination"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).offset(offset).limit(limit).all()
    
    def get_message_count(self, conversation_id: int) -> int:
        """Compter le nombre de messages dans une conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()
    
    def get_user_conversations(self, user_id: int, offset: int = 0, limit: int = 20) -> List[Conversation]:
        """Récupérer les conversations d'un utilisateur"""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(desc(Conversation.updated_at)).offset(offset).limit(limit).all()
    
    def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """Récupérer le dernier message d'une conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).first()
    
    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Supprimer une conversation"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        # Supprimer tous les messages de la conversation
        self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()
        
        # Supprimer la conversation
        self.db.delete(conversation)
        self.db.commit()
        
        return True
    
    def update_conversation_title(self, conversation_id: int, user_id: int, new_title: str) -> Optional[Conversation]:
        """Mettre à jour le titre d'une conversation"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        conversation.title = new_title
        conversation.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def get_chat_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtenir les statistiques de chat d'un utilisateur"""
        conversation_count = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).count()
        
        message_count = self.db.query(Message).join(Conversation).filter(
            Conversation.user_id == user_id
        ).count()
        
        return {
            "conversation_count": conversation_count,
            "message_count": message_count,
            "user_id": user_id
        }