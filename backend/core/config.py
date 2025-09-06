import os
from typing import Optional, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, PostgresDsn
from functools import lru_cache
import logging
import json


class Settings(BaseSettings):
    APP_NAME: str = "RAG FAQ Chatbot"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Chatbot intelligent basé sur RAG pour la gestion des FAQ d'entreprise"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", json_schema_extra={'env': 'ENV'})
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    WORKERS: int = 1
    
    SECRET_KEY: str = Field(..., min_length=32, json_schema_extra={'env': 'SECRET_KEY'})
    JWT_SECRET_KEY: str = Field(..., min_length=32, json_schema_extra={'env': 'JWT_SECRET_KEY'})
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12
    
    DATABASE_URL: PostgresDsn = Field(..., json_schema_extra={'env': 'DATABASE_URL'}) 
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    TEST_DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode='before')
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "sqlite:///")):
            raise ValueError("DATABASE_URL doit commencer par postgresql:// ou sqlite:///")
        return v
    
    REDIS_URL: str = Field(default="redis://localhost:6379/0", json_schema_extra={'env': 'REDIS_URL'})
    REDIS_CACHE_TTL: int = 3600
    REDIS_SESSION_TTL: int = 86400
    
    # Configuration OpenRouter/DeepSeek (remplace Ollama)
    OPENROUTER_API_KEY: str = Field(..., json_schema_extra={'env': 'OPENROUTER_API_KEY'})
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1", json_schema_extra={'env': 'OPENROUTER_BASE_URL'})
    OPENROUTER_MODEL: str = Field(default="deepseek/deepseek-chat", json_schema_extra={'env': 'OPENROUTER_MODEL'})
    OPENROUTER_MAX_TOKENS: int = Field(default=4096, json_schema_extra={'env': 'OPENROUTER_MAX_TOKENS'})
    OPENROUTER_TEMPERATURE: float = Field(default=0.7, json_schema_extra={'env': 'OPENROUTER_TEMPERATURE'})
    OPENROUTER_TOP_P: float = Field(default=0.9, json_schema_extra={'env': 'OPENROUTER_TOP_P'})
    OPENROUTER_TIMEOUT: int = Field(default=120, json_schema_extra={'env': 'OPENROUTER_TIMEOUT'})
    OPENROUTER_MAX_RETRIES: int = Field(default=3, json_schema_extra={'env': 'OPENROUTER_MAX_RETRIES'})
    OPENROUTER_STREAM: bool = Field(default=True, json_schema_extra={'env': 'OPENROUTER_STREAM'})
    
    # Modèles disponibles sur OpenRouter pour DeepSeek
    AVAILABLE_DEEPSEEK_MODELS: List[str] = [
        "deepseek/deepseek-chat",
        "deepseek/deepseek-coder", 
        "deepseek/deepseek-r1",
        "deepseek/deepseek-r1-distill-llama-70b",
        "deepseek/deepseek-r1-distill-qwen-32b"
    ]
    
    @field_validator("OPENROUTER_TEMPERATURE", mode='before') 
    @classmethod
    def validate_temperature(cls, v):
        if isinstance(v, str):
            try:
                v = float(v)
            except ValueError:
                raise ValueError("OPENROUTER_TEMPERATURE doit être un nombre valide")
        
        if not 0.0 <= v <= 2.0:
            raise ValueError("OPENROUTER_TEMPERATURE doit être entre 0.0 et 2.0")
        return v
    
    @field_validator("OPENROUTER_TOP_P", mode='before')
    @classmethod  
    def validate_top_p(cls, v):
        if isinstance(v, str):
            try:
                v = float(v)
            except ValueError:
                raise ValueError("OPENROUTER_TOP_P doit être un nombre valide")
        
        if not 0.0 <= v <= 1.0:
            raise ValueError("OPENROUTER_TOP_P doit être entre 0.0 et 1.0")
        return v
    
    @field_validator("OPENROUTER_MODEL", mode='before')
    @classmethod
    def validate_openrouter_model(cls, v):
        # Validation plus flexible pour OpenRouter
        if not v or not isinstance(v, str):
            raise ValueError("OPENROUTER_MODEL doit être une chaîne non vide")
        return v
    
    # Configuration des modèles d'embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DEVICE: str = Field(default="cpu", json_schema_extra={'env': 'EMBEDDING_DEVICE'})
    EMBEDDING_NORMALIZE: bool = True
    
    # Configuration ChromaDB
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8001
    CHROMADB_COLLECTION_NAME: str = "faq_documents"
    CHROMADB_PERSIST_DIRECTORY: str = "./data/chromadb"
    CHROMADB_DISTANCE_METRIC: str = "cosine"
    
    # Autres bases de données vectorielles (optionnelles)
    PINECONE_API_KEY: Optional[str] = Field(None, json_schema_extra={'env': 'PINECONE_API_KEY'})
    PINECONE_ENVIRONMENT: Optional[str] = Field(None, json_schema_extra={'env': 'PINECONE_ENVIRONMENT'})
    PINECONE_INDEX_NAME: str = "faq-chatbot"
    
    WEAVIATE_URL: Optional[str] = Field(None, json_schema_extra={'env': 'WEAVIATE_URL'})
    WEAVIATE_API_KEY: Optional[str] = Field(None, json_schema_extra={'env': 'WEAVIATE_API_KEY'})
    
    # Configuration RAG optimisée pour DeepSeek
    RAG_CHUNK_SIZE: int = Field(default=1000, json_schema_extra={'env': 'RAG_CHUNK_SIZE'})
    RAG_CHUNK_OVERLAP: int = Field(default=200, json_schema_extra={'env': 'RAG_CHUNK_OVERLAP'})
    RAG_TOP_K_DOCUMENTS: int = Field(default=5, json_schema_extra={'env': 'RAG_TOP_K_DOCUMENTS'})
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.6, json_schema_extra={'env': 'RAG_SIMILARITY_THRESHOLD'})
    RAG_MAX_CONTEXT_LENGTH: int = Field(default=8000, json_schema_extra={'env': 'RAG_MAX_CONTEXT_LENGTH'})
    RAG_RERANK_DOCUMENTS: bool = Field(default=False, json_schema_extra={'env': 'RAG_RERANK_DOCUMENTS'})
    RAG_USE_METADATA_FILTERING: bool = Field(default=True, json_schema_extra={'env': 'RAG_USE_METADATA_FILTERING'})
    
    # Prompts système optimisés pour DeepSeek
    RAG_SYSTEM_PROMPT: str = Field(
        default="""Tu es un assistant IA expert qui répond aux questions en utilisant une base de connaissances.

Instructions importantes :
- Réponds UNIQUEMENT en te basant sur le contexte fourni
- Si tu ne trouves pas l'information dans le contexte, dis "Je ne trouve pas cette information dans la base de connaissances"
- Sois précis, concis et professionnel
- Cite les sources quand pertinent (nom du document)
- N'invente jamais d'informations
- Structure tes réponses clairement
- Réponds en français""",
        json_schema_extra={'env': 'RAG_SYSTEM_PROMPT'}
    )
    
    # Templates pour DeepSeek (format OpenAI compatible)
    DEEPSEEK_CONTEXT_TEMPLATE: str = """Voici le contexte de la base de connaissances:

{context}

Question: {question}

Réponds en te basant uniquement sur ce contexte. Si l'information n'est pas disponible, indique-le clairement."""
    
    # Configuration des fichiers
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE: int = UPLOAD_MAX_SIZE
    UPLOAD_ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx", ".md", ".csv", ".json"]
    UPLOAD_DIRECTORY: str = "./uploads/data"
    UPLOAD_DIR: str = UPLOAD_DIRECTORY
    DOCUMENTS_DIRECTORY: str = "./data/documents"
    MAX_CONCURRENT_UPLOADS: int = 3
    
    # Configuration des logs
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    LOG_MAX_SIZE: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5
        
    @field_validator("LOG_LEVEL", mode='before')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL doit être un de: {valid_levels}")
        return v.upper()
    
    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        json_schema_extra={'env': 'CORS_ORIGINS'}
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "X-Client-Version"
    ]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    RATE_LIMIT_BURST: int = 20
    RATE_LIMIT_PER_USER: int = 50
    RATE_LIMIT_WINDOW: int = 3600
    
    # WebSocket settings
    WEBSOCKET_PING_INTERVAL: int = 20
    WEBSOCKET_PING_TIMEOUT: int = 10
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    
    # Monitoring and metrics
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_ENDPOINT: str = "/health"
    
    # Cache
    CACHE_TTL_EMBEDDINGS: int = 86400
    CACHE_TTL_RESPONSES: int = 3600
    CACHE_TTL_DOCUMENTS: int = 7200
    CACHE_TTL_SEARCH_RESULTS: int = 1800
    
    # User and conversation limits
    MAX_CONVERSATION_HISTORY: int = 50
    MAX_DAILY_REQUESTS_PER_USER: int = 1000
    DEFAULT_RESPONSE_LANGUAGE: str = "fr"
    SUPPORTED_LANGUAGES: List[str] = ["fr", "en", "es", "de"]
    MAX_CONVERSATION_TURNS: int = 20
    
    # Admin settings
    ADMIN_EMAIL: Optional[str] = Field(None, json_schema_extra={'env': 'ADMIN_EMAIL'})
    ADMIN_PASSWORD: Optional[str] = Field(None, json_schema_extra={'env': 'ADMIN_PASSWORD'})
    
    # Email settings
    SMTP_HOST: Optional[str] = Field(None, json_schema_extra={'env': 'SMTP_HOST'})
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = Field(None, json_schema_extra={'env': 'SMTP_USERNAME'})
    SMTP_PASSWORD: Optional[str] = Field(None, json_schema_extra={'env': 'SMTP_PASSWORD'})
    SMTP_USE_TLS: bool = True
    
    # Analytics
    GOOGLE_ANALYTICS_ID: Optional[str] = Field(None, json_schema_extra={'env': 'GOOGLE_ANALYTICS_ID'})
    
    # Frontend-specific settings
    FRONTEND_URL: str = Field(default="http://localhost:3000", json_schema_extra={'env': 'FRONTEND_URL'})
    
    # Sécurité
    ENABLE_API_KEY_AUTH: bool = Field(default=False, json_schema_extra={'env': 'ENABLE_API_KEY_AUTH'})
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_REQUEST_LOGGING: bool = Field(default=True, json_schema_extra={'env': 'ENABLE_REQUEST_LOGGING'})
    MAX_REQUEST_SIZE: int = 50 * 1024 * 1024
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if not v or v == "":
            return [
                "http://localhost:3000",
                "http://localhost:5173", 
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]
        
        if isinstance(v, list):
            return v
            
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            if origins:
                return origins
        
        return [
            "http://localhost:3000",
            "http://localhost:5173", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ]
    
    @property
    def openrouter_url(self) -> str:
        """URL complète d'OpenRouter"""
        return self.OPENROUTER_BASE_URL
    
    def get_openrouter_config(self) -> dict:
        """Obtenir la configuration complète pour OpenRouter/DeepSeek"""
        return {
            "api_key": self.OPENROUTER_API_KEY,
            "base_url": self.OPENROUTER_BASE_URL,
            "model": self.OPENROUTER_MODEL,
            "max_tokens": self.OPENROUTER_MAX_TOKENS,
            "temperature": self.OPENROUTER_TEMPERATURE,
            "top_p": self.OPENROUTER_TOP_P,
            "timeout": self.OPENROUTER_TIMEOUT,
            "max_retries": self.OPENROUTER_MAX_RETRIES,
            "stream": self.OPENROUTER_STREAM,
        }
    
    def format_deepseek_prompt(self, prompt: str, context: str = None) -> str:
        """Formater un prompt pour DeepSeek"""
        if context:
            return self.DEEPSEEK_CONTEXT_TEMPLATE.format(context=context, question=prompt)
        return prompt
    
    @property
    def database_url_async(self) -> str:
        return str(self.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ["development", "dev", "local"]
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ["production", "prod"]
    
    @property
    def log_level_int(self) -> int:
        return getattr(logging, self.LOG_LEVEL)


def validate_environment():
    """Valider les variables d'environnement requises pour OpenRouter"""
    settings = get_settings()
    
    required_vars = [
        "SECRET_KEY",
        "JWT_SECRET_KEY", 
        "DATABASE_URL",
        "OPENROUTER_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
    
    # Validation spécifique à OpenRouter
    openrouter_config = settings.get_openrouter_config()
    if not openrouter_config["api_key"]:
        raise ValueError("OPENROUTER_API_KEY est requis")
    
    return True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def is_feature_enabled(feature: str) -> bool:
    """Vérifier si une fonctionnalité spécifique est activée"""
    settings = get_settings()
    feature_map = {
        "metrics": settings.ENABLE_METRICS,
        "debug": settings.DEBUG,
        "openrouter": bool(settings.OPENROUTER_API_KEY),
        "streaming": settings.OPENROUTER_STREAM,
        "reranking": settings.RAG_RERANK_DOCUMENTS,
        "metadata_filtering": settings.RAG_USE_METADATA_FILTERING,
    }
    return feature_map.get(feature, False)


def get_model_info() -> dict:
    """Informations sur les modèles utilisés"""
    settings = get_settings()
    
    return {
        "llm": {
            "provider": "OpenRouter",
            "model": settings.OPENROUTER_MODEL,
            "max_tokens": settings.OPENROUTER_MAX_TOKENS,
            "temperature": settings.OPENROUTER_TEMPERATURE,
            "base_url": settings.OPENROUTER_BASE_URL,
        },
        "embedding": {
            "model": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIMENSION,
            "device": settings.EMBEDDING_DEVICE,
        },
        "vector_db": {
            "provider": "ChromaDB",
            "collection": settings.CHROMADB_COLLECTION_NAME,
            "distance_metric": settings.CHROMADB_DISTANCE_METRIC,
        }
    }


settings = get_settings()