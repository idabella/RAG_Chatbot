from fastapi import APIRouter

from api.v1.endpoints import auth, chat, documents,admin 

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Non autorise"},
        403: {"description": "Accès interdit"},
    }
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"],
    responses={
        401: {"description": "Non autorise"},
        429: {"description": "Trop de requêtes"},
        500: {"description": "Erreur serveur"},
    }
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
    responses={
        401: {"description": "Non autorise"},
        403: {"description": "Accès interdit"},
        413: {"description": "Fichier trop volumineux"},
        415: {"description": "Format de fichier non supporte"},
    }
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["administration"],
    responses={
        401: {"description": "Non autorise"},
        403: {"description": "Accès administrateur requis"},
        404: {"description": "Ressource non trouvee"},
    }
)



@api_router.get(
    "/health",
    tags=["system"],
    summary="Verification de l'etat de l'API",
    description="Endpoint pour verifier que l'API fonctionne correctement"
)
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "RAG FAQ Chatbot API is running"
    }

@api_router.get(
    "/info",
    tags=["system"],
    summary="Informations sur l'API",
    description="Retourne les informations sur la version et les fonctionnalites de l'API"
)
async def api_info():
    return {
        "name": "RAG FAQ Chatbot API",
        "version": "1.0.0",
        "description": "API pour chatbot intelligent base sur RAG",
        "features": [
            "Authentification JWT",
            "Chat en temps reel",
            "Gestion de documents FAQ",
            "Recherche vectorielle",
            "Interface d'administration"
        ],
        "endpoints": {
            "auth": "/api/v1/auth",
            "chat": "/api/v1/chat", 
            "documents": "/api/v1/documents",
            "admin": "/api/v1/admin"
        }
    }

