import os
import sys

# Force tf-keras usage before any TensorFlow imports
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['KERAS_BACKEND'] = 'tensorflow'

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging
from typing import Dict, List
import json
from datetime import datetime
from sqlalchemy.orm import Session
import httpx

from core.config import settings
from core.database import init_db, close_db, get_db
from api.v1.api import api_router
from services.chat_service import ChatService
from services.rag_service import RAGService
from services.embedding_service import EmbeddingService
from services.document_service import DocumentService
from utils.logging import setup_logging
from schemas.chat import ChatRequest, ChatResponse

setup_logging()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
        
        logger.info(f"WebSocket connection established: {connection_id}")
    
    def disconnect(self, connection_id: str, user_id: str = None):
        self.active_connections.pop(connection_id, None)

        if user_id and user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_personal_message(message, connection_id)

    async def broadcast(self, message: dict):
        for connection_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, connection_id)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting RAG Chatbot Application...")
    
    try:
        logger.info("📊 Initializing database...")
        init_db()
        
        logger.info("🤖 Initializing services...")
        
        # Initialiser les services dans l'ordre correct
        try:
            embedding_service = EmbeddingService()
            logger.info("🔧 Initializing EmbeddingService...")
            await embedding_service.initialize()
            logger.info("✅ EmbeddingService initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize EmbeddingService: {e}")
            raise
        
        try:
            rag_service = RAGService(embedding_service)
            logger.info("🔧 Initializing RAGService...")
            await rag_service.initialize()
            logger.info("✅ RAGService initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAGService: {e}")
            raise
        
        # Stocker les services dans l'état de l'application
        app.state.embedding_service = embedding_service
        app.state.rag_service = rag_service
        app.state.connection_manager = manager
        
        logger.info("✅ Application started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}", exc_info=True)
        raise
    
    logger.info("🔄 Shutting down RAG Chatbot Application...")
    
    try:
        # Fermer toutes les connexions WebSocket
        for connection_id in list(manager.active_connections.keys()):
            websocket = manager.active_connections[connection_id]
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket {connection_id}: {e}")
        
        # Nettoyer les services
        if hasattr(app.state, 'rag_service'):
            await app.state.rag_service.cleanup()
            
        if hasattr(app.state, 'embedding_service'):
            await app.state.embedding_service.cleanup()
        
        close_db()
        
        logger.info("✅ Application shutdown completed!")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


def setup_middlewares(app: FastAPI):
    """Setup all middlewares for the FastAPI app"""
    
    # Trusted host middleware (security)
    if hasattr(settings, 'is_production') and settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.yourdomain.com", "yourdomain.com"]  # Update with your domain
        )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # CORS middleware - CRITICAL for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=["*"],  # Allow frontend to read all headers
    )


setup_middlewares(app)

# Static files for uploaded documents
if not hasattr(settings, 'is_production') or not settings.is_production:
    app.mount("/static", StaticFiles(directory="uploads/data"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    """Factory function to create ChatService with proper dependencies"""
    return ChatService(db=db, rag_service=app.state.rag_service)


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Factory function to create DocumentService with proper dependencies"""
    return DocumentService(db=db, embedding_service=app.state.embedding_service)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception for {request.url}: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if hasattr(settings, 'is_production') and settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": "An unexpected error occurred"
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{connection_id}")
async def websocket_chat_endpoint(websocket: WebSocket, connection_id: str):
    await manager.connect(websocket, connection_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            logger.info(f"Received WebSocket message: {message_data}")
            
            message_type = message_data.get("type", "chat")
            
            if message_type == "chat":
                await handle_chat_message(websocket, connection_id, message_data)
            elif message_type == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": message_data.get("timestamp")}, 
                    connection_id
                )
            elif message_type == "join_room":
                user_id = message_data.get("user_id")
                if user_id:
                    if user_id not in manager.user_connections:
                        manager.user_connections[user_id] = []
                    if connection_id not in manager.user_connections[user_id]:
                        manager.user_connections[user_id].append(connection_id)
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


async def handle_chat_message(websocket: WebSocket, connection_id: str, message_data: dict):
    db: Session = None
    try:
        user_message = message_data.get("message", "")
        user_id = message_data.get("user_id", 1)  # Default user_id si pas fourni
        conversation_id = message_data.get("conversation_id")
        
        if not user_message.strip():
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "Message cannot be empty"
                },
                connection_id
            )
            return
        
        # Send typing indicator
        await manager.send_personal_message(
            {
                "type": "typing",
                "is_typing": True
            },
            connection_id
        )
        
        # Créer une session DB pour le WebSocket
        db = next(get_db())
        
        # Créer le ChatService avec les bonnes dépendances
        chat_service = ChatService(db=db, rag_service=app.state.rag_service)
        
        # Créer l'objet ChatRequest
        chat_request = ChatRequest(
            message=user_message,
            conversation_id=conversation_id,
            context=message_data.get("context", {})
        )
        
        # Traiter le message
        response = await chat_service.process_message(user_id=user_id, message_request=chat_request)
        
        # Stop typing indicator
        await manager.send_personal_message(
            {
                "type": "typing",
                "is_typing": False
            },
            connection_id
        )
        
        # Send response
        await manager.send_personal_message(
            {
                "type": "message",
                "message": response.message,
                "message_id": response.message_id,
                "conversation_id": response.conversation_id,
                "sources": response.sources,
                "confidence": response.confidence,
                "timestamp": response.timestamp.isoformat() if response.timestamp else datetime.utcnow().isoformat()
            },
            connection_id
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        
        # Stop typing indicator on error
        await manager.send_personal_message(
            {
                "type": "typing",
                "is_typing": False
            },
            connection_id
        )
        
        await manager.send_personal_message(
            {
                "type": "error",
                "message": f"Sorry, I encountered an error: {str(e)}"
            },
            connection_id
        )
    finally:
        # Fermer la session DB
        if db:
            db.close()


def _get_recommendations(diagnostic: dict) -> List[str]:
    """Générer des recommandations basées sur le diagnostic"""
    recommendations = []
    
    status = diagnostic.get("status", "unknown")
    
    if status == "working":
        recommendations.append("✅ Votre configuration Claude fonctionne parfaitement!")
        
    elif status == "auth_error":
        recommendations.extend([
            "🔧 Vérifiez votre clé API Claude dans le fichier .env",
            "🔧 Assurez-vous qu'elle commence par 'sk-ant-api03-'",
            "🔧 Générez une nouvelle clé sur console.anthropic.com si nécessaire"
        ])
        
    elif status == "quota_exceeded":
        recommendations.extend([
            "📊 Vérifiez votre utilisation sur console.anthropic.com",
            "📊 Vous avez peut-être atteint la limite gratuite mensuelle",
            "💳 Considérez un upgrade vers un plan payant",
            "⏰ Attendez la réinitialisation mensuelle du quota gratuit"
        ])
        
    elif status == "api_error":
        recommendations.extend([
            "🔧 Vérifiez que le modèle spécifié existe",
            "🔧 Certains modèles nécessitent un compte payant",
            "📞 Contactez le support Anthropic si le problème persiste"
        ])
        
    elif status == "connection_error":
        recommendations.extend([
            "🌐 Vérifiez votre connexion Internet",
            "🔒 Vérifiez les paramètres de firewall/proxy",
            "🔄 Réessayez dans quelques minutes"
        ])
        
    else:
        recommendations.append("🔍 Problème non identifié - vérifiez les logs pour plus de détails")
    
    return recommendations


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RAG FAQ Chatbot API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else None,
        "status": "online",
        "frontend_urls": {
            "development": ["http://localhost:3000", "http://localhost:5173"],
            "production": settings.CORS_ORIGINS
        }
    }


# Health check endpoint for both backend monitoring and frontend connection testing
@app.get("/health")
async def health_check():
    try:
        checks = {
            "database": "ok",
            "embedding_service": "ok" if hasattr(app.state, 'embedding_service') and app.state.embedding_service else "error",
            "rag_service": "ok" if hasattr(app.state, 'rag_service') and app.state.rag_service else "error",
            "websocket_connections": len(manager.active_connections)
        }
        
        status_code = "healthy" if all(
            v == "ok" if isinstance(v, str) else True 
            for v in checks.values()
        ) else "unhealthy"
        
        return {
            "status": status_code,
            "checks": checks,
            "timestamp": str(datetime.utcnow()),
            "cors_origins": settings.CORS_ORIGINS,
            "environment": getattr(settings, 'ENVIRONMENT', 'development')
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": str(datetime.utcnow())
            }
        )


# API connection test endpoint specifically for frontend
@app.get("/api/v1/test")
async def api_connection_test():
    """Simple endpoint to test frontend-backend connection"""
    return {
        "success": True,
        "message": "Backend connection successful",
        "timestamp": datetime.utcnow().isoformat(),
        "cors_enabled": True
    }


# Endpoint de test pour le service RAG
@app.post("/api/v1/test-rag")
async def test_rag_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Endpoint pour tester le service RAG"""
    try:
        chat_service = ChatService(db=db, rag_service=app.state.rag_service)
        response = await chat_service.process_message(user_id=1, message_request=request)
        return response
    except Exception as e:
        logger.error(f"Error in test RAG endpoint: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# ============ ENDPOINTS DE DIAGNOSTIC CLAUDE ============

@app.get("/api/v1/diagnostic/claude")
async def claude_api_diagnostic():
    """Diagnostic complet de l'API Claude"""
    try:
        if hasattr(app.state, 'rag_service') and app.state.rag_service:
            diagnostic = await app.state.rag_service.diagnose_api_status()
            
            return {
                "success": True,
                "diagnostic": diagnostic,
                "recommendations": _get_recommendations(diagnostic)
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "RAG Service non initialisé",
                    "diagnostic": None
                }
            )
            
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic Claude: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "diagnostic": None
            }
        )


@app.get("/api/v1/test/claude-simple")
async def test_claude_simple():
    """Test simple de l'API Claude avec diagnostic détaillé"""
    try:
        headers = {
            "x-api-key": settings.CLAUDE_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": settings.CLAUDE_MODEL,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        logger.info("🧪 Test simple de l'API Claude...")
        logger.info(f"🔑 Clé API configurée: {'Oui' if settings.CLAUDE_API_KEY else 'Non'}")
        logger.info(f"🤖 Modèle: {settings.CLAUDE_MODEL}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 200
            status_message = "✅ API Claude fonctionne!" if success else f"❌ Erreur {response.status_code}"
            
            logger.info(f"📊 Résultat du test: {status_message}")
            
            result = {
                "success": success,
                "status_code": response.status_code,
                "status_message": status_message,
                "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text,
                "api_key_configured": bool(settings.CLAUDE_API_KEY),
                "api_key_preview": settings.CLAUDE_API_KEY[:10] + "..." if settings.CLAUDE_API_KEY else "❌ Non configurée",
                "model_used": settings.CLAUDE_MODEL,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Ajouter des détails spécifiques selon le code d'erreur
            if not success:
                if response.status_code == 401:
                    result["error_type"] = "authentication"
                    result["suggestion"] = "🔧 Vérifiez votre clé API Claude dans le fichier .env"
                elif response.status_code == 429:
                    result["error_type"] = "quota_or_rate_limit"
                    result["suggestion"] = "📊 Quota épuisé ou limite de taux dépassée"
                elif response.status_code == 400:
                    result["error_type"] = "bad_request"
                    result["suggestion"] = "⚙️ Vérifiez la configuration du modèle"
                elif response.status_code == 403:
                    result["error_type"] = "forbidden"
                    result["suggestion"] = "🚪 Ce modèle nécessite peut-être un compte payant"
                else:
                    result["error_type"] = "unknown"
                    result["suggestion"] = "❓ Erreur inattendue"
            
            return result
            
    except httpx.TimeoutException:
        logger.error("⏰ Timeout lors du test de l'API Claude")
        return {
            "success": False,
            "error": "Timeout - Impossible de joindre l'API Claude",
            "error_type": "timeout",
            "suggestion": "🌐 Vérifiez votre connexion Internet",
            "api_key_configured": bool(settings.CLAUDE_API_KEY)
        }
    except Exception as e:
        logger.error(f"💥 Erreur lors du test Claude: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "exception", 
            "suggestion": "🔧 Vérifiez votre configuration",
            "api_key_configured": bool(settings.CLAUDE_API_KEY)
        }


@app.get("/api/v1/diagnostic/config")
async def diagnostic_config():
    """Diagnostic de la configuration Claude"""
    try:
        config_check = {
            "claude_api_key_configured": bool(settings.CLAUDE_API_KEY),
            "claude_api_key_format": "valide" if settings.CLAUDE_API_KEY and settings.CLAUDE_API_KEY.startswith("sk-ant-api03-") else "invalide",
            "claude_model": settings.CLAUDE_MODEL,
            "claude_max_tokens": settings.CLAUDE_MAX_TOKENS,
            "claude_temperature": settings.CLAUDE_TEMPERATURE,
            "debug_mode": settings.DEBUG,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Masquer les caractères sensibles de la clé API
        if settings.CLAUDE_API_KEY:
            config_check["claude_api_key_preview"] = settings.CLAUDE_API_KEY[:15] + "..." + settings.CLAUDE_API_KEY[-5:]
        
        # Évaluer la santé de la configuration
        issues = []
        if not settings.CLAUDE_API_KEY:
            issues.append("❌ Clé API Claude manquante")
        elif not settings.CLAUDE_API_KEY.startswith("sk-ant-api03-"):
            issues.append("⚠️ Format de clé API suspect")
        
        if not settings.DEBUG and settings.ENVIRONMENT == "development":
            issues.append("⚠️ DEBUG désactivé en développement")
        
        config_check["issues"] = issues
        config_check["health"] = "good" if not issues else "warning" if len(issues) == 1 else "error"
        
        return {
            "success": True,
            "config": config_check
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic config: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True
    )