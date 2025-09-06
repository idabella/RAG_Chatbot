import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional, List
from datetime import datetime
import time
from dataclasses import dataclass

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterResponse:
    """Classe pour représenter une réponse d'OpenRouter"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    created: Optional[int] = None


class OpenRouterService:
    """Service pour interagir avec DeepSeek via OpenRouter API"""
    
    def __init__(self):
        self.config = settings.get_openrouter_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        
        # Headers pour les requêtes
        self.headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",  # Requis par OpenRouter
            "X-Title": settings.APP_NAME,
        }
        
    async def initialize(self):
        """Initialiser le service OpenRouter"""
        try:
            # Créer la session HTTP
            timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.headers
            )
            
            # Tester la connexion
            await self.health_check()
            
            self._initialized = True
            logger.info(f"OpenRouter Service initialisé avec le modèle: {self.config['model']}")
            
        except Exception as e:
            logger.error(f"Erreur initialisation OpenRouter Service: {str(e)}")
            raise
    
    async def cleanup(self):
        """Nettoyer les ressources"""
        if self.session and not self.session.closed:
            await self.session.close()
        self._initialized = False
        logger.info("OpenRouter Service nettoyé")
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifier la santé du service OpenRouter"""
        try:
            if not self.session:
                return {
                    "status": "unhealthy",
                    "error": "Session non initialisée",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test simple avec un prompt minimal
            test_response = await self._make_request(
                messages=[
                    {"role": "system", "content": "Tu es un assistant test."},
                    {"role": "user", "content": "Dis juste 'OK' pour confirmer que tu fonctionnes."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            if test_response.content.strip():
                return {
                    "status": "healthy",
                    "model": self.config['model'],
                    "base_url": self.config['base_url'],
                    "test_response": test_response.content[:50] + "..." if len(test_response.content) > 50 else test_response.content,
                    "usage": test_response.usage,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "degraded",
                    "error": "Réponse vide du modèle",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur health check OpenRouter: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Générer une réponse avec DeepSeek via OpenRouter"""
        try:
            if not self._initialized or not self.session:
                raise RuntimeError("Service OpenRouter non initialisé")
            
            # Construire les messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Générer la réponse
            response = await self._make_request(
                messages=messages,
                max_tokens=max_tokens or self.config['max_tokens'],
                temperature=temperature or self.config['temperature']
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Erreur génération réponse OpenRouter: {str(e)}")
            raise
    
    async def generate_response_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """Générer une réponse en streaming"""
        try:
            if not self._initialized or not self.session:
                raise RuntimeError("Service OpenRouter non initialisé")
            
            # Construire les messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Générer en streaming
            async for chunk in self._make_request_stream(
                messages=messages,
                max_tokens=max_tokens or self.config['max_tokens'],
                temperature=temperature or self.config['temperature']
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Erreur génération streaming OpenRouter: {str(e)}")
            yield f"Erreur: {str(e)}"
    
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None
    ) -> OpenRouterResponse:
        """Effectuer une requête vers OpenRouter"""
        url = f"{self.config['base_url']}/chat/completions"
        
        payload = {
            "model": self.config['model'],
            "messages": messages,
            "max_tokens": max_tokens or self.config['max_tokens'],
            "temperature": temperature or self.config['temperature'],
            "top_p": top_p or self.config['top_p'],
            "stream": False
        }
        
        retries = 0
        while retries <= self.config['max_retries']:
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extraire le contenu
                        content = ""
                        if "choices" in data and len(data["choices"]) > 0:
                            choice = data["choices"][0]
                            if "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]
                        
                        return OpenRouterResponse(
                            content=content,
                            model=data.get("model", self.config['model']),
                            usage=data.get("usage"),
                            finish_reason=data.get("choices", [{}])[0].get("finish_reason"),
                            created=data.get("created")
                        )
                    
                    elif response.status == 429:  # Rate limit
                        wait_time = 2 ** retries
                        logger.warning(f"Rate limit atteint, attente de {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        retries += 1
                        continue
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Erreur OpenRouter {response.status}: {error_text}")
                        raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                retries += 1
                if retries > self.config['max_retries']:
                    raise
                logger.warning(f"Timeout, retry {retries}/{self.config['max_retries']}")
                await asyncio.sleep(1)
            
            except Exception as e:
                if retries >= self.config['max_retries']:
                    raise
                retries += 1
                logger.warning(f"Erreur requête, retry {retries}/{self.config['max_retries']}: {str(e)}")
                await asyncio.sleep(1)
        
        raise Exception(f"Échec après {self.config['max_retries']} tentatives")
    
    async def _make_request_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None
    ) -> AsyncGenerator[str, None]:
        """Effectuer une requête streaming vers OpenRouter"""
        url = f"{self.config['base_url']}/chat/completions"
        
        payload = {
            "model": self.config['model'],
            "messages": messages,
            "max_tokens": max_tokens or self.config['max_tokens'],
            "temperature": temperature or self.config['temperature'],
            "top_p": top_p or self.config['top_p'],
            "stream": True
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
                
                # Lire le stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    # Ignorer les lignes vides et les commentaires
                    if not line or line.startswith(':'):
                        continue
                    
                    # Parser les lignes SSE
                    if line.startswith('data: '):
                        data_str = line[6:]  # Enlever 'data: '
                        
                        # Fin du stream
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extraire le contenu
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                    if content:
                                        yield content
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Erreur streaming OpenRouter: {str(e)}")
            yield f"Erreur streaming: {str(e)}"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Obtenir la liste des modèles disponibles sur OpenRouter"""
        try:
            url = f"{self.config['base_url']}/models"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filtrer les modèles DeepSeek
                    deepseek_models = [
                        model for model in data.get("data", [])
                        if "deepseek" in model.get("id", "").lower()
                    ]
                    
                    return deepseek_models
                else:
                    logger.error(f"Erreur récupération modèles: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur get_available_models: {str(e)}")
            return []
    
    async def get_model_info(self, model_id: str = None) -> Dict[str, Any]:
        """Obtenir les informations d'un modèle spécifique"""
        target_model = model_id or self.config['model']
        
        try:
            models = await self.get_available_models()
            
            for model in models:
                if model.get("id") == target_model:
                    return {
                        "id": model.get("id"),
                        "name": model.get("name", ""),
                        "description": model.get("description", ""),
                        "context_length": model.get("context_length", 0),
                        "pricing": model.get("pricing", {}),
                        "top_provider": model.get("top_provider", {}),
                    }
            
            return {"error": f"Modèle {target_model} non trouvé"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques d'utilisation (placeholder)"""
        return {
            "provider": "OpenRouter",
            "model": self.config['model'],
            "base_url": self.config['base_url'],
            "initialized": self._initialized,
            "session_active": self.session is not None and not self.session.closed
        }