import os
import sys
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging
from contextlib import contextmanager
from typing import Generator
from alembic.config import Config

from core.config import settings

# Force utf-8 on Windows - amélioré
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Forcer l'encoding pour stdout/stderr
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)


class DatabaseManager:    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        # Skip connection test during initialization to avoid startup failures
        self._setup_engines(test_connection=False)
    
    def _get_database_url_safely(self):
        """Get database URL with encoding error handling"""
        try:
            # Essayer d'abord avec settings
            if hasattr(settings, 'DATABASE_URL'):
                database_url = settings.DATABASE_URL
                
                # Si c'est un objet PostgresDsn de Pydantic, le convertir en string
                if hasattr(database_url, '__str__'):
                    database_url_str = str(database_url)
                    logger.info("Successfully converted PostgresDsn to string")
                    return database_url_str
                elif isinstance(database_url, str):
                    logger.info("Using DATABASE_URL from settings")
                    return database_url
                else:
                    logger.warning(f"Unexpected DATABASE_URL type: {type(database_url)}")
                    
        except (UnicodeDecodeError, AttributeError) as e:
            logger.warning(f"Could not get DATABASE_URL from settings: {e}")
        
        # Fallback sur l'URL hardcodée qui fonctionne
        logger.info("Using fallback database URL")
        return "postgresql://mustapha:Yufn6191@localhost:5432/ragdb"
    
    def _setup_engines(self, test_connection=True):        
        """Setup database engines with proper configuration"""
        database_url = self._get_database_url_safely()
        
        # Configuration d'engine optimisée
        engine_kwargs = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "echo": False,  # Désactivé en production, activez pour debug
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "connect_args": {
                "client_encoding": "utf8",
                "application_name": "rag_chatbot"
            }
        }

        try:
            self.engine = create_engine(database_url, **engine_kwargs)
            
            # Test de connexion seulement si demandé
            if test_connection:
                self._test_connection()
            
            # Configuration de session avec auto-flush activé
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=True,  # IMPORTANT: Active l'auto-flush
                bind=self.engine
            )
            logger.info("Database engine setup successful")
            
        except Exception as e:
            logger.error(f"Error setting up database engine: {e}")
            if test_connection:
                raise
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()
                if test_result and test_result[0] == 1:
                    logger.info("Database connection test successful")
                    return True
                else:
                    logger.error("Database connection test failed - unexpected result")
                    return False
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def ensure_connection(self):
        """Ensure database connection is working - call this before operations"""
        if not self._test_connection():
            logger.warning("Database connection failed, reinitializing...")
            self._setup_engines(test_connection=True)
        return True
    
    def create_tables(self):
        """Create all database tables"""
        try:
            # S'assurer que la connexion fonctionne
            self.ensure_connection()
            
            # Importer tous les modèles pour s'assurer qu'ils sont enregistrés
            try:
                from models import user, conversation, document, message
                logger.info("All models imported successfully")
            except ImportError as e:
                logger.warning(f"Could not import some models: {e}")
                # Continuer quand même - les modèles pourraient être importés ailleurs
            
            # Créer toutes les tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("All tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            if "codec can't decode" in str(e).lower():
                logger.error("UTF-8 encoding issue detected")
                logger.info("Try running: ALTER DATABASE ragdb SET client_encoding TO 'utf-8';")
            
            raise
    
    def drop_tables(self):
        """Drop all tables (debug mode only)"""
        debug_mode = getattr(settings, 'DEBUG', False)
        if not debug_mode:
            raise Exception("Table deletion is only allowed in debug mode")
        
        try:
            self.ensure_connection()
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All tables have been dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        return self.SessionLocal()
    
    def close(self):
        """Close all database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI qui fournit une session de base de données
    avec commit automatique en cas de succès
    """
    db = db_manager.get_session()
    try:
        yield db
        # COMMIT AUTOMATIQUE - C'est la correction principale
        db.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        logger.debug("Database session rolled back")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


@contextmanager
def get_db_context():
    """
    Context manager pour les opérations de base de données
    avec commit automatique
    """
    db = db_manager.get_session()
    try:
        yield db
        db.commit()
        logger.debug("Database context committed successfully")
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        logger.debug("Database context rolled back")
        raise
    finally:
        db.close()
        logger.debug("Database context closed")


def get_db_manual() -> Generator[Session, None, None]:
    """
    Version manuelle sans auto-commit pour les cas où vous voulez 
    contrôler manuellement les transactions
    """
    db = db_manager.get_session()
    try:
        yield db
        # Pas de commit automatique ici
    except Exception as e:
        logger.error(f"Manual DB session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class AlembicConfig:    
    """Configuration pour les migrations Alembic"""
    
    @staticmethod
    def get_config():
        """Get Alembic configuration"""
        alembic_cfg = Config() 
        alembic_cfg.set_main_option("script_location", "alembic")
        
        # Obtenir l'URL de base de données de manière sûre
        database_url = db_manager._get_database_url_safely()
        
        # S'assurer que c'est une string pour Alembic
        if not isinstance(database_url, str):
            database_url = str(database_url)
            
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        return alembic_cfg
    
    @staticmethod
    def create_migration(message: str):
        """Create a new Alembic migration"""
        try:
            from alembic import command
            config = AlembicConfig.get_config()
            command.revision(config, autogenerate=True, message=message)
            logger.info(f"Migration created: {message}")
        except Exception as e:
            logger.error(f"Error creating migration: {e}")
            raise
    
    @staticmethod
    def run_migrations():
        """Run all pending Alembic migrations"""
        try:
            from alembic import command
            config = AlembicConfig.get_config()
            command.upgrade(config, "head")
            logger.info("All migrations executed successfully")
        except Exception as e:
            logger.error(f"Error executing migrations: {e}")
            raise
    
    @staticmethod
    def rollback_migration(revision: str = "-1"):
        """Rollback Alembic migration"""
        try:
            from alembic import command
            config = AlembicConfig.get_config()
            command.downgrade(config, revision)
            logger.info(f"Migration rolled back to: {revision}")
        except Exception as e:
            logger.error(f"Error rolling back migration: {e}")
            raise


def init_db():
    """Initialize the database (create tables)"""
    try:
        logger.info("Initializing database...")
        db_manager.create_tables()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def close_db():
    """Close all database connections"""
    try:
        db_manager.close()
        logger.info("Database closed successfully")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


def test_database_connection():
    """Test database connection and basic operations"""
    try:
        logger.info("Testing database connection...")
        
        # Test de connexion simple
        if not db_manager._test_connection():
            logger.error("Basic connection test failed")
            return False
        
        # Test d'écriture/lecture
        with get_db_context() as db:
            # Créer une table de test
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY, 
                    test_value VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insérer une valeur de test
            result = db.execute(text("""
                INSERT INTO test_connection (test_value) 
                VALUES (:value) RETURNING id
            """), {"value": "test_connection_success"})
            
            test_id = result.fetchone()[0]
            logger.info(f"Test record inserted with ID: {test_id}")
            
            # Vérifier que la valeur a été insérée
            check_result = db.execute(text("""
                SELECT test_value FROM test_connection WHERE id = :id
            """), {"id": test_id})
            
            retrieved_value = check_result.fetchone()[0]
            
            if retrieved_value == "test_connection_success":
                logger.info("Database read/write test SUCCESSFUL")
                
                # Nettoyer la table de test
                db.execute(text("DROP TABLE IF EXISTS test_connection"))
                return True
            else:
                logger.error("Database read/write test FAILED - value mismatch")
                return False
                
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def reset_database():
    """Reset database (drop and recreate tables) - DEBUG MODE ONLY"""
    try:
        debug_mode = getattr(settings, 'DEBUG', False)
        if not debug_mode:
            raise Exception("Database reset is only allowed in debug mode")
        
        logger.warning("Resetting database...")
        db_manager.drop_tables()
        db_manager.create_tables()
        logger.info("Database reset completed")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise


# Export des éléments principaux
__all__ = [
    'Base',
    'db_manager',
    'get_db',
    'get_db_context',
    'get_db_manual',
    'init_db',
    'close_db',
    'test_database_connection',
    'reset_database',
    'AlembicConfig',
]


# Auto-initialisation au démarrage (optionnel)
def startup_database():
    """Fonction à appeler au démarrage de l'application"""
    try:
        logger.info("Starting database initialization...")
        
        # Tester la connexion
        if test_database_connection():
            logger.info("Database connection test passed")
        else:
            logger.warning("Database connection test failed, but continuing...")
        
        # Initialiser les tables
        init_db()
        
        logger.info("Database startup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        return False


if __name__ == "__main__":
    # Test du module quand exécuté directement
    startup_database()