#!/usr/bin/env python3
"""
Script de nettoyage ChromaDB
À placer dans: backend/cleanup_chromadb.py

Usage:
cd backend
python cleanup_chromadb.py
"""

import chromadb
import sys
import os
from pathlib import Path

# Ajouter le path du projet pour importer les settings
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.config import settings
    CHROMADB_PATH = settings.CHROMADB_PERSIST_DIRECTORY
    COLLECTION_NAME = settings.CHROMADB_COLLECTION_NAME
except ImportError:
    # Fallback avec le chemin correct vers data/
    CHROMADB_PATH = "./data/chroma_db"  # Chemin corrigé
    COLLECTION_NAME = "faq_documents"
    print("⚠️ Utilisation des valeurs par défaut (pas d'accès aux settings)")

def cleanup_chromadb():
    """Nettoie directement la base ChromaDB"""
    
    print("🔧 Script de nettoyage ChromaDB")
    print(f"📁 Chemin ChromaDB: {CHROMADB_PATH}")
    print(f"📦 Collection: {COLLECTION_NAME}")
    
    try:
        # Vérifier que le dossier existe
        if not os.path.exists(CHROMADB_PATH):
            print(f"❌ Dossier ChromaDB non trouvé: {CHROMADB_PATH}")
            print("💡 Vérifiez que le chemin est correct ou que ChromaDB a été initialisé")
            return
        
        print("🔌 Connexion à ChromaDB...")
        client = chromadb.PersistentClient(path=CHROMADB_PATH)
        
        # Récupérer la collection
        try:
            collection = client.get_collection(COLLECTION_NAME)
            print(f"✅ Collection '{COLLECTION_NAME}' trouvée")
        except Exception as e:
            print(f"❌ Collection '{COLLECTION_NAME}' non trouvée: {e}")
            
            # Lister les collections disponibles
            try:
                collections = client.list_collections()
                if collections:
                    print("📋 Collections disponibles:")
                    for col in collections:
                        print(f"  - {col.name}")
                else:
                    print("📋 Aucune collection trouvée")
            except:
                pass
            return
        
        # Afficher les statistiques
        count = collection.count()
        print(f"📊 Nombre total de chunks: {count}")
        
        if count == 0:
            print("✅ Collection déjà vide")
            return
        
        # Lister quelques documents pour info
        print("\n📄 Échantillon de documents:")
        try:
            results = collection.get(limit=10, include=["metadatas"])
            
            if not results.get("metadatas"):
                print("  Aucune métadonnée disponible")
            else:
                documents = {}
                for metadata in results["metadatas"]:
                    doc_id = metadata.get("document_id", "unknown")
                    source_file = metadata.get("source_file", metadata.get("filename", "unknown"))
                    if doc_id not in documents:
                        documents[doc_id] = {
                            "source_file": source_file,
                            "chunks": 0
                        }
                    documents[doc_id]["chunks"] += 1
                
                for doc_id, info in documents.items():
                    print(f"  📄 {doc_id[:30]}...")
                    print(f"     └── Source: {info['source_file']}")
                    print(f"     └── Chunks: {info['chunks']}")
        
        except Exception as e:
            print(f"⚠️ Erreur listage: {e}")
        
        # Menu de choix
        print(f"\n🤔 Que voulez-vous faire?")
        print("1. Supprimer UN document spécifique par ID")
        print("2. Supprimer par nom de fichier")
        print("3. Supprimer TOUS les documents (⚠️ DANGER)")
        print("4. Afficher plus d'informations")
        print("5. Annuler")
        
        while True:
            choice = input("\nVotre choix (1/2/3/4/5): ").strip()
            
            if choice == "1":
                # Suppression d'un document spécifique
                print("\n📋 Documents disponibles:")
                try:
                    results = collection.get(limit=50, include=["metadatas"])
                    doc_ids = set()
                    for metadata in results["metadatas"]:
                        doc_id = metadata.get("document_id")
                        if doc_id:
                            doc_ids.add(doc_id)
                    
                    for i, doc_id in enumerate(sorted(doc_ids), 1):
                        print(f"  {i}. {doc_id}")
                
                except Exception as e:
                    print(f"Erreur listage: {e}")
                
                doc_id = input("\nID du document à supprimer (copiez-collez): ").strip()
                if doc_id:
                    try:
                        # Compter avant suppression
                        before_results = collection.get(where={"document_id": doc_id})
                        before_count = len(before_results["ids"]) if before_results.get("ids") else 0
                        
                        if before_count == 0:
                            print(f"❌ Document '{doc_id}' non trouvé")
                        else:
                            # Supprimer
                            collection.delete(where={"document_id": doc_id})
                            print(f"✅ Document '{doc_id}' supprimé ({before_count} chunks)")
                            
                    except Exception as e:
                        print(f"❌ Erreur suppression: {e}")
                break
            
            elif choice == "2":
                # Suppression par nom de fichier
                filename = input("\nNom de fichier (ou partie du nom): ").strip()
                if filename:
                    try:
                        # Chercher les documents avec ce nom
                        all_results = collection.get(include=["metadatas"])
                        
                        to_delete_docs = {}
                        for metadata in all_results["metadatas"]:
                            source_file = metadata.get("source_file", metadata.get("filename", ""))
                            if filename.lower() in source_file.lower():
                                doc_id = metadata.get("document_id")
                                if doc_id:
                                    to_delete_docs[doc_id] = source_file
                        
                        if to_delete_docs:
                            print(f"\n📋 Trouvé {len(to_delete_docs)} document(s) correspondant(s):")
                            for doc_id, source_file in to_delete_docs.items():
                                print(f"  📄 {doc_id}")
                                print(f"     └── {source_file}")
                            
                            confirm = input(f"\nSupprimer ces {len(to_delete_docs)} document(s)? (oui/non): ")
                            if confirm.lower() in ["oui", "yes", "y"]:
                                deleted_count = 0
                                for doc_id in to_delete_docs.keys():
                                    try:
                                        collection.delete(where={"document_id": doc_id})
                                        deleted_count += 1
                                        print(f"✅ Supprimé: {doc_id}")
                                    except Exception as e:
                                        print(f"⚠️ Erreur suppression {doc_id}: {e}")
                                
                                print(f"\n🎉 Supprimé {deleted_count}/{len(to_delete_docs)} documents")
                            else:
                                print("❌ Suppression annulée")
                        else:
                            print(f"❌ Aucun document trouvé contenant '{filename}'")
                            
                    except Exception as e:
                        print(f"❌ Erreur recherche: {e}")
                break
            
            elif choice == "3":
                # Suppression de tous les documents
                print("⚠️ ⚠️ ⚠️  ATTENTION  ⚠️ ⚠️ ⚠️")
                print("Vous allez supprimer TOUS les documents de la collection!")
                print(f"Cela représente {count} chunks au total.")
                
                confirm = input("\nÊtes-vous absolument sûr? Tapez 'SUPPRIMER TOUT' pour confirmer: ")
                if confirm == "SUPPRIMER TOUT":
                    try:
                        # Supprimer tous les documents
                        all_results = collection.get()
                        all_ids = all_results["ids"]
                        
                        if all_ids:
                            # Supprimer par batch pour éviter les timeouts
                            batch_size = 100
                            deleted_total = 0
                            
                            print(f"🗑️ Suppression de {len(all_ids)} chunks par batch de {batch_size}...")
                            
                            for i in range(0, len(all_ids), batch_size):
                                batch_ids = all_ids[i:i + batch_size]
                                collection.delete(ids=batch_ids)
                                deleted_total += len(batch_ids)
                                print(f"   Supprimé {deleted_total}/{len(all_ids)} chunks...")
                            
                            final_count = collection.count()
                            print(f"✅ Suppression terminée!")
                            print(f"   Initial: {count} chunks")
                            print(f"   Final: {final_count} chunks")
                            print(f"   Supprimé: {count - final_count} chunks")
                        else:
                            print("❌ Aucun chunk à supprimer")
                            
                    except Exception as e:
                        print(f"❌ Erreur suppression globale: {e}")
                else:
                    print("❌ Suppression annulée (confirmation incorrecte)")
                break
            
            elif choice == "4":
                # Afficher plus d'informations
                try:
                    print(f"\n📊 Informations détaillées:")
                    print(f"   Chemin ChromaDB: {CHROMADB_PATH}")
                    print(f"   Collection: {COLLECTION_NAME}")
                    print(f"   Total chunks: {count}")
                    
                    # Taille du dossier ChromaDB
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(CHROMADB_PATH):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            total_size += os.path.getsize(filepath)
                    
                    print(f"   Taille sur disque: {total_size / 1024 / 1024:.2f} MB")
                    
                    # Échantillon plus large
                    results = collection.get(limit=50, include=["metadatas", "documents"])
                    
                    if results.get("documents"):
                        avg_chunk_size = sum(len(doc) for doc in results["documents"]) / len(results["documents"])
                        print(f"   Taille moyenne chunk: {avg_chunk_size:.0f} caractères")
                    
                    # Grouper par document
                    documents = {}
                    for metadata in results.get("metadatas", []):
                        doc_id = metadata.get("document_id", "unknown")
                        if doc_id not in documents:
                            documents[doc_id] = {
                                "source": metadata.get("source_file", "unknown"),
                                "chunks": 0
                            }
                        documents[doc_id]["chunks"] += 1
                    
                    print(f"   Documents uniques: {len(documents)}")
                    
                    if documents:
                        print(f"\n📄 Détail des documents:")
                        for doc_id, info in list(documents.items())[:10]:  # Limiter à 10
                            print(f"   📄 {doc_id[:40]}...")
                            print(f"      Source: {info['source']}")
                            print(f"      Chunks: {info['chunks']}")
                    
                except Exception as e:
                    print(f"Erreur affichage détails: {e}")
                
                # Revenir au menu
                continue
            
            elif choice == "5":
                print("❌ Opération annulée")
                break
            
            else:
                print("❌ Choix invalide, réessayez")
                continue
    
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_chromadb()