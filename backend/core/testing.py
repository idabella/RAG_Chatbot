#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la connexion et le fonctionnement de la base de données PostgreSQL
"""

import os
import sys
import traceback
from datetime import datetime

# Ajouter le répertoire parent au path pour importer les modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_basic_connection():
    """Test de connexion basique avec psycopg2"""
    print("=" * 60)
    print("🔍 TEST 1: Connexion basique avec psycopg2")
    print("=" * 60)
    
    try:
        import psycopg2
        
        # Paramètres de connexion (ajustez selon votre configuration)
        conn_params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'ragdb',
            'user': 'postgres',
            'password': 'asensio21'
        }
        
        print(f"📡 Tentative de connexion à: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        # Test de connexion
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Test simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connexion réussie!")
        print(f"📋 Version PostgreSQL: {version[0][:50]}...")
        
        # Test d'encodage
        cursor.execute("SHOW client_encoding;")
        encoding = cursor.fetchone()
        print(f"📝 Encodage client: {encoding[0]}")
        
        cursor.execute("SHOW server_encoding;")
        server_encoding = cursor.fetchone()
        print(f"🖥️  Encodage serveur: {server_encoding[0]}")
        
        # Test avec caractères français
        cursor.execute("SELECT 'Test éàèùç ñ' as test_utf8;")
        utf8_test = cursor.fetchone()
        print(f"🔤 Test UTF-8: {utf8_test[0]}")
        
        cursor.close()
        conn.close()
        print("✅ Test psycopg2 réussi!\n")
        return True
        
    except ImportError:
        print("❌ psycopg2 n'est pas installé")
        print("💡 Installez avec: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        return False


def test_sqlalchemy_connection():
    """Test de connexion avec SQLAlchemy"""
    print("=" * 60)
    print("🔍 TEST 2: Connexion SQLAlchemy")
    print("=" * 60)
    
    try:
        from sqlalchemy import create_engine, text
        
        # URL de connexion
        database_url = "postgresql://postgres:d1ma385db123@localhost:5432/ragdb"
        print(f"📡 URL de connexion: {database_url}")
        
        # Créer le moteur
        engine = create_engine(
            database_url,
            connect_args={"client_encoding": "utf8"},
            echo=False
        )
        
        # Test de connexion
        with engine.connect() as conn:
            # Test simple
            result = conn.execute(text("SELECT 1 as test;"))
            test_result = result.fetchone()
            print(f"✅ Test simple: {test_result[0]}")
            
            # Test d'encodage
            result = conn.execute(text("SELECT 'Bonjour éàèùç!' as greeting;"))
            greeting = result.fetchone()
            print(f"🔤 Test UTF-8: {greeting[0]}")
            
            # Informations sur la base
            result = conn.execute(text("SELECT current_database();"))
            db_name = result.fetchone()
            print(f"🗄️  Base de données: {db_name[0]}")
            
            result = conn.execute(text("SELECT current_user;"))
            user = result.fetchone()
            print(f"👤 Utilisateur: {user[0]}")
        
        print("✅ Test SQLAlchemy réussi!\n")
        return True
        
    except ImportError as e:
        print(f"❌ Module manquant: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur SQLAlchemy: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        traceback.print_exc()
        return False


def test_project_database():
    """Test avec le gestionnaire de base de données du projet"""
    print("=" * 60)
    print("🔍 TEST 3: Gestionnaire de DB du projet")
    print("=" * 60)
    
    try:
        # Importer le gestionnaire de base de données
        from core.database import db_manager
        
        print("📦 Import du db_manager réussi")
        
        # Test de connexion
        print("🔌 Test de connexion...")
        connection_ok = db_manager._test_connection()
        
        if connection_ok:
            print("✅ Connexion au gestionnaire DB réussie!")
            
            # Test de session
            print("📋 Test de création de session...")
            session = db_manager.get_session()
            print("✅ Session créée avec succès!")
            session.close()
            print("🔒 Session fermée")
            
        else:
            print("❌ Échec de la connexion au gestionnaire DB")
            return False
            
        print("✅ Test gestionnaire de projet réussi!\n")
        return True
        
    except ImportError as e:
        print(f"❌ Impossible d'importer le gestionnaire: {e}")
        print("💡 Assurez-vous que core/database.py existe")
        return False
    except Exception as e:
        print(f"❌ Erreur du gestionnaire: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        traceback.print_exc()
        return False


def test_table_creation():
    """Test de création d'une table simple"""
    print("=" * 60)
    print("🔍 TEST 4: Création de table de test")
    print("=" * 60)
    
    try:
        from sqlalchemy import create_engine, text, Column, Integer, String, DateTime
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.sql import func
        from sqlalchemy.orm import sessionmaker
        
        # URL de connexion
        database_url = "postgresql://postgres:d1ma385db123@localhost:5432/ragdb"
        
        # Créer le moteur et la base
        engine = create_engine(database_url, connect_args={"client_encoding": "utf8"})
        Base = declarative_base()
        
        # Définir une table de test
        class TestTable(Base):
            __tablename__ = 'test_connection_table'
            
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            message = Column(String(255))
            created_at = Column(DateTime(timezone=True), server_default=func.now())
        
        print("📋 Modèle de table défini")
        
        # Créer la table
        print("🔨 Création de la table...")
        Base.metadata.create_all(engine)
        print("✅ Table créée avec succès!")
        
        # Test d'insertion
        print("📝 Test d'insertion de données...")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        test_record = TestTable(
            name="Test Connection",
            message="Bonjour depuis le test de connexion! éàèùç"
        )
        
        session.add(test_record)
        session.commit()
        print("✅ Données insérées!")
        
        # Test de lecture
        print("📖 Test de lecture...")
        records = session.query(TestTable).all()
        print(f"📊 Nombre d'enregistrements: {len(records)}")
        
        for record in records:
            print(f"   ID: {record.id}, Nom: {record.name}")
            print(f"   Message: {record.message}")
            print(f"   Créé le: {record.created_at}")
        
        session.close()
        
        # Nettoyer (supprimer la table de test)
        print("🧹 Suppression de la table de test...")
        Base.metadata.drop_all(engine)
        print("✅ Table supprimée!")
        
        print("✅ Test création de table réussi!\n")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de table: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        traceback.print_exc()
        return False


def main():
    """Fonction principale pour exécuter tous les tests"""
    print("🚀 TESTS DE CONNEXION BASE DE DONNÉES")
    print("=" * 60)
    print(f"⏰ Démarré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Compteur de tests réussis
    tests_passed = 0
    total_tests = 4
    
    # Exécuter tous les tests
    if test_basic_connection():
        tests_passed += 1
    
    if test_sqlalchemy_connection():
        tests_passed += 1
    
    if test_project_database():
        tests_passed += 1
        
    if test_table_creation():
        tests_passed += 1
    
    # Résumé final
    print("=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"✅ Tests réussis: {tests_passed}/{total_tests}")
    print(f"❌ Tests échoués: {total_tests - tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Tous les tests sont passés! Votre base de données est prête!")
        print("💡 Vous pouvez maintenant démarrer votre application avec:")
        print("   uvicorn main:app --reload")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print(f"⏰ Terminé le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()