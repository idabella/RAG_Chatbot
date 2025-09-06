# services/embedding_service_improved.py - VERSION CORRIGÉE POUR ISOLATION DES DOCUMENTS
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

from core.config import settings
from utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.model = None
        self.chroma_client = None
        self.collection = None
        self.executor = None
        self.text_processor = TextProcessor()
        
        self.chroma_settings = Settings(
            persist_directory=settings.CHROMADB_PERSIST_DIRECTORY,
            anonymized_telemetry=False
        )
    
    async def initialize(self):
        try:
            logger.info(f"Chargement du modèle d'embeddings: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="embedding")
            
            logger.info("Initialisation de ChromaDB")
            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMADB_PERSIST_DIRECTORY
            )
            
            self.collection = await self._get_or_create_collection()
            
            stats = await self.get_collection_stats()
            logger.info(f"Collection stats après initialisation: {stats}")
            
            logger.info("Service d'embeddings initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service d'embeddings: {e}")
            raise
    
    async def cleanup(self):
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
        logger.info("Service d'embeddings nettoyé")
    
    async def _get_or_create_collection(self):
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=settings.CHROMADB_COLLECTION_NAME,
                metadata={"description": "FAQ Documents Embeddings"}
            )
            
            logger.info(f"Collection ChromaDB '{settings.CHROMADB_COLLECTION_NAME}' prête")
            return collection
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la collection: {e}")
            raise
    
    def _prepare_chromadb_metadata(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoyer les métadonnées pour ChromaDB avec meilleure isolation"""
        clean_metadata = {}
        
        for key, value in metadata_dict.items():
            if value is None:
                clean_metadata[key] = ""
            elif isinstance(value, dict):
                # Aplatir les dictionnaires
                for sub_key, sub_value in value.items():
                    new_key = f"{key}_{sub_key}"
                    clean_metadata[new_key] = str(sub_value) if sub_value is not None else ""
            elif isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list):
                clean_metadata[key] = ", ".join(str(item) for item in value if item)
            else:
                clean_metadata[key] = str(value)
        
        return clean_metadata
    
    async def generate_embedding(self, text: str) -> List[float]:
        try:
            if not self.executor:
                raise RuntimeError("EmbeddingService non initialisé")
            
            if not text or not text.strip():
                logger.warning("Texte vide fourni pour embedding")
                return []
            
            cleaned_text = self.text_processor.clean_text(text)
            
            if not cleaned_text or len(cleaned_text.strip()) < 3:
                logger.warning(f"Texte trop court après nettoyage: '{cleaned_text}'")
                return []
            
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor, 
                self._generate_embedding_sync, 
                cleaned_text
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'embedding: {e}")
            raise
    
    def _generate_embedding_sync(self, text: str) -> np.ndarray:
        return self.model.encode([text], convert_to_numpy=True)[0]
    
    # *** AMÉLIORATION MAJEURE : Meilleure isolation des documents ***
    async def index_document(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> bool:
        try:
            if not content or not content.strip():
                logger.warning(f"Contenu vide pour le document {document_id}")
                return False
            
            logger.info(f"🔄 Indexation document {document_id} - Taille: {len(content)} caractères")
            
            # *** FIX CRITIQUE : Supprimer TOUS les anciens chunks de ce document ***
            try:
                # Utiliser document_id exact pour éviter les fuites entre documents
                self.collection.delete(where={"document_id": {"$eq": str(document_id)}})
                logger.info(f"🗑️ Tous les anciens chunks du document {document_id} supprimés")
            except Exception as e:
                logger.warning(f"Erreur suppression anciens chunks: {e}")
            
            # *** AMÉLIORATION : Extraction plus précise des informations personnelles ***
            person_info = self._extract_person_information(content, metadata)
            logger.info(f"👤 Informations de la personne détectées: {person_info.get('name', 'Non détecté')}")
            
            # Chunking intelligent avec isolation renforcée
            chunks = self._create_isolated_chunks(content, metadata, person_info, document_id)
            
            if not chunks:
                logger.warning(f"Aucun chunk généré pour {document_id}")
                return False
            
            logger.info(f"📄 Document {document_id} divisé en {len(chunks)} chunks isolés")
            
            # Générer les embeddings avec préfixes d'isolation
            chunk_texts = []
            chunk_metadata = []
            chunk_ids = []
            
            for i, chunk_data in enumerate(chunks):
                if not chunk_data["text"].strip():
                    continue
                    
                # *** FIX : ID unique plus robuste ***
                chunk_id = f"{document_id}_chunk_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk_data["text"])
                
                # *** MÉTADONNÉES ENRICHIES AVEC ISOLATION FORTE ***
                base_meta = {
                    "document_id": str(document_id),
                    "chunk_id": chunk_id,
                    "chunk_index": int(i),
                    "chunk_size": int(len(chunk_data["original_text"])),
                    "timestamp": datetime.now().isoformat(),
                    "chunk_type": chunk_data["chunk_type"],
                    "section_title": chunk_data.get("section_title", ""),
                    "keywords": ", ".join(chunk_data["keywords"][:10]),
                    "content_preview": chunk_data["original_text"][:200] + "..." if len(chunk_data["original_text"]) > 200 else chunk_data["original_text"],
                    
                    # *** NOUVEAUX CHAMPS D'ISOLATION ***
                    "person_name": person_info.get("name", ""),
                    "person_name_normalized": person_info.get("name_normalized", ""),
                    "person_email": person_info.get("email", ""),
                    "person_phone": person_info.get("phone", ""),
                    "document_type": person_info.get("document_type", "cv"),
                    "isolation_key": f"{document_id}_{person_info.get('name_normalized', 'unknown')}",
                    
                    # Contexte renforcé
                    "document_context": f"Document de {person_info.get('name', 'personne inconnue')} - {chunk_data['chunk_type']}",
                    "unique_document_signature": f"{document_id}_{hash(content[:500]) % 10000}"
                }
                
                # Ajouter métadonnées personnalisées si disponibles
                if metadata:
                    try:
                        clean_custom_metadata = self._prepare_chromadb_metadata(metadata)
                        base_meta.update(clean_custom_metadata)
                    except Exception as e:
                        logger.warning(f"Erreur métadonnées personnalisées: {e}")
                
                chunk_metadata.append(base_meta)
            
            if not chunk_texts:
                logger.warning(f"Aucun chunk valide après filtrage pour {document_id}")
                return False
            
            # Générer embeddings
            try:
                embeddings = await self._generate_embeddings_batch(chunk_texts)
                if not embeddings or len(embeddings) != len(chunk_texts):
                    logger.error(f"Erreur génération embeddings: {len(embeddings)} vs {len(chunk_texts)}")
                    return False
            except Exception as e:
                logger.error(f"Erreur génération embeddings batch: {e}")
                return False
            
            # Stocker dans ChromaDB
            try:
                self.collection.add(
                    ids=chunk_ids,
                    embeddings=embeddings,
                    documents=chunk_texts,
                    metadatas=chunk_metadata
                )
                logger.info(f"✅ Document {document_id} indexé avec {len(chunks)} chunks isolés")
                return True
                
            except Exception as e:
                logger.error(f"Erreur stockage ChromaDB pour {document_id}: {e}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur indexation document {document_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _extract_person_information(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """*** NOUVEAU : Extraction précise des informations personnelles ***"""
        person_info = {"document_type": "cv"}
        
        # 1. Extraction du nom depuis les métadonnées
        if metadata:
            if metadata.get("student_name"):
                person_info["name"] = metadata["student_name"]
            elif metadata.get("name"):
                person_info["name"] = metadata["name"]
        
        # 2. Extraction du nom depuis le contenu si pas trouvé
        if not person_info.get("name"):
            name_patterns = [
                # Patterns plus robustes pour les noms
                r'^\s*([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+(?:\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+)?)\s*$',
                r'Nom\s*:?\s*([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+(?:\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+)+)',
                r'([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿç]+)\s*\n.*(?:Ingénieur|Développeur|Étudiant)',
                r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ]{2,}\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ]{2,})\s*$'
            ]
            
            lines = content.split('\n')[:15]  # Chercher dans les 15 premières lignes
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5 or len(line) > 60:
                    continue
                    
                for pattern in name_patterns:
                    match = re.search(pattern, line, re.MULTILINE)
                    if match:
                        potential_name = match.group(1).strip()
                        # Valider que c'est bien un nom
                        words = potential_name.split()
                        if (2 <= len(words) <= 4 and 
                            all(len(w) >= 2 and w.isalpha() for w in words) and
                            not any(word.lower() in ['formation', 'expérience', 'contact', 'projet', 'stage'] for word in words)):
                            person_info["name"] = potential_name
                            break
                if person_info.get("name"):
                    break
        
        # 3. Normaliser le nom pour l'isolation
        if person_info.get("name"):
            normalized_name = re.sub(r'[^a-zA-Z\s]', '', person_info["name"].lower())
            normalized_name = re.sub(r'\s+', '_', normalized_name.strip())
            person_info["name_normalized"] = normalized_name
        
        # 4. Extraire email et téléphone
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        if email_match:
            person_info["email"] = email_match.group()
        
        phone_patterns = [
            r'(?:\+33|0)[1-9](?:[0-9]{8})',
            r'(?:\+212|0)[5-7][0-9]{8}',
            r'\b\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}\b'
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, content)
            if phone_match:
                person_info["phone"] = phone_match.group()
                break
        
        return person_info
    
    def _create_isolated_chunks(
        self, 
        content: str, 
        metadata: Dict[str, Any], 
        person_info: Dict[str, Any],
        document_id: str
    ) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Créer des chunks avec isolation renforcée ***"""
        try:
            chunks = []
            
            # 1. Détecter les sections principales
            sections = self._detect_sections(content)
            
            # 2. Créer un préfixe d'isolation unique pour ce document
            isolation_prefix = self._create_isolation_prefix(person_info, document_id)
            
            if sections:
                logger.info(f"📑 Sections détectées: {[s['title'] for s in sections]}")
                
                # Traiter chaque section avec isolation
                for section in sections:
                    section_chunks = self._chunk_section_with_isolation(
                        section, person_info, metadata, isolation_prefix
                    )
                    chunks.extend(section_chunks)
            else:
                # Fallback: chunking classique mais avec isolation
                logger.info("📄 Pas de sections détectées, chunking classique avec isolation")
                basic_chunks = self.text_processor.chunk_text(
                    content, 
                    chunk_size=settings.RAG_CHUNK_SIZE, 
                    overlap=settings.RAG_CHUNK_OVERLAP
                )
                
                for i, chunk_text in enumerate(basic_chunks):
                    if len(chunk_text.strip()) < 20:
                        continue
                        
                    keywords = self._extract_keywords(chunk_text)
                    chunk_type = self._identify_chunk_type(chunk_text)
                    
                    # *** Enrichir avec isolation forte ***
                    enriched_text = self._enrich_chunk_with_isolation(
                        chunk_text, person_info, keywords, chunk_type, isolation_prefix, ""
                    )
                    
                    chunks.append({
                        "text": enriched_text,
                        "original_text": chunk_text,
                        "keywords": keywords,
                        "chunk_type": chunk_type,
                        "section_title": "",
                        "person_info": person_info,
                        "isolation_prefix": isolation_prefix
                    })
            
            logger.info(f"✅ {len(chunks)} chunks isolés créés")
            return chunks
            
        except Exception as e:
            logger.error(f"Erreur création chunks isolés: {e}")
            # Fallback sécurisé
            try:
                basic_chunks = self.text_processor.chunk_text(content, 500, 50)
                isolation_prefix = f"[DOCUMENT:{document_id}|PERSONNE:{person_info.get('name', 'INCONNU')}]"
                return [{
                    "text": f"{isolation_prefix}\n{chunk}", 
                    "original_text": chunk, 
                    "keywords": [], 
                    "chunk_type": "general", 
                    "section_title": "",
                    "person_info": person_info,
                    "isolation_prefix": isolation_prefix
                } for chunk in basic_chunks if len(chunk.strip()) > 10]
            except:
                return []
    
    def _create_isolation_prefix(self, person_info: Dict[str, Any], document_id: str) -> str:
        """*** NOUVEAU : Créer un préfixe d'isolation unique ***"""
        prefix_parts = [f"DOCUMENT_ID:{document_id}"]
        
        if person_info.get("name"):
            prefix_parts.append(f"PERSONNE:{person_info['name']}")
        
        if person_info.get("email"):
            prefix_parts.append(f"EMAIL:{person_info['email']}")
        
        return "[" + "|".join(prefix_parts) + "]"
    
    def _chunk_section_with_isolation(
        self, 
        section: Dict[str, Any], 
        person_info: Dict[str, Any],
        metadata: Dict[str, Any],
        isolation_prefix: str
    ) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Chunker une section avec isolation ***"""
        chunks = []
        section_content = section["content"].strip()
        section_title = section["title"]
        
        # Ajuster la taille des chunks selon le type de section
        if section_title.lower() in ['contact', 'langues', 'certifications']:
            max_chunk_size = len(section_content)
            overlap = 0
        else:
            max_chunk_size = settings.RAG_CHUNK_SIZE
            overlap = settings.RAG_CHUNK_OVERLAP
        
        # Chunking du contenu
        if len(section_content) <= max_chunk_size:
            section_chunks = [section_content]
        else:
            section_chunks = self.text_processor.chunk_text(
                section_content, max_chunk_size, overlap
            )
        
        # Traiter chaque chunk de la section avec isolation
        for i, chunk_text in enumerate(section_chunks):
            if len(chunk_text.strip()) < 15:
                continue
            
            keywords = self._extract_keywords(chunk_text, section_title)
            chunk_type = self._identify_chunk_type_from_section(section_title, chunk_text)
            
            # *** Enrichir avec isolation de section ***
            enriched_text = self._enrich_chunk_with_isolation(
                chunk_text, person_info, keywords, chunk_type, isolation_prefix, section_title
            )
            
            chunks.append({
                "text": enriched_text,
                "original_text": chunk_text,
                "keywords": keywords,
                "chunk_type": chunk_type,
                "section_title": section_title,
                "person_info": person_info,
                "isolation_prefix": isolation_prefix
            })
        
        return chunks
    
    def _enrich_chunk_with_isolation(
        self, 
        chunk: str, 
        person_info: Dict[str, Any],
        keywords: List[str], 
        chunk_type: str,
        isolation_prefix: str,
        section_title: str = ""
    ) -> str:
        """*** NOUVEAU : Enrichir un chunk avec isolation forte ***"""
        
        # Construire le préfixe de contexte avec isolation
        context_parts = []
        
        # *** ISOLATION FORTE : Toujours mentionner la personne ***
        if person_info.get("name"):
            context_parts.append(f"CANDIDAT: {person_info['name']}")
        else:
            context_parts.append("CANDIDAT: PERSONNE_INCONNUE")
        
        # Section actuelle
        if section_title:
            context_parts.append(f"SECTION: {section_title}")
        
        # Type de contenu
        type_labels = {
            "education": "FORMATION_ET_EDUCATION",
            "experience": "EXPERIENCE_PROFESSIONNELLE", 
            "project": "PROJETS_ET_REALISATIONS",
            "skills": "COMPETENCES_ET_EXPERTISE",
            "certification": "CERTIFICATIONS_ET_DIPLOMES",
            "contact": "INFORMATIONS_CONTACT",
            "languages": "LANGUES",
            "personal_info": "INFORMATIONS_PERSONNELLES",
            "general": "INFORMATIONS_GENERALES"
        }
        
        if chunk_type in type_labels:
            context_parts.append(f"TYPE: {type_labels[chunk_type]}")
        
        # Mots-clés principaux
        if keywords:
            main_keywords = keywords[:5]
            context_parts.append(f"MOTS_CLES: {', '.join(main_keywords)}")
        
        # *** CONSTRUIRE LE TEXTE AVEC ISOLATION MAXIMALE ***
        isolation_header = f"{isolation_prefix}\n"
        context_header = "[" + " | ".join(context_parts) + "]\n"
        
        # Le chunk final avec triple isolation
        final_chunk = (
            isolation_header +
            context_header +
            f"--- CONTENU DE {person_info.get('name', 'PERSONNE_INCONNUE')} ---\n" +
            chunk +
            f"\n--- FIN CONTENU {person_info.get('name', 'PERSONNE_INCONNUE')} ---"
        )
        
        return final_chunk
    
    # *** MÉTHODES EXISTANTES GARDÉES ***
    def _detect_sections(self, content: str) -> List[Dict[str, Any]]:
        """Détecter les sections dans le document"""
        sections = []
        
        section_patterns = [
            r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ\s]{3,50})(?:\s*:?\s*)?$',
            r'^\s*([IVX]+[\.\)]\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][A-Za-zàâäéèêëïîôöùûüÿç\s]{5,50})',
            r'^\s*([0-9]+[\.\)]\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][A-Za-zàâäéèêëïîôöùûüÿç\s]{5,50})',
            r'^\s*(FORMATION|EXPÉRIENCE|COMPÉTENCES|PROJETS|CERTIFICATIONS|LANGUES|CONTACT|PROFIL|OBJECTIF|DIPLÔMES)S?\s*:?\s*$',
            r'^\s*(Formation|Expérience|Compétences|Projets|Certifications|Langues|Contact|Profil|Objectif|Diplômes)s?\s*:?\s*$'
        ]
        
        lines = content.split('\n')
        current_section = {"title": "Introduction", "start": 0, "content": ""}
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            is_section_title = False
            section_title = None
            
            for pattern in section_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    section_title = match.group(1).strip()
                    if 5 <= len(section_title) <= 50 and not re.search(r'\d{4}', section_title):
                        is_section_title = True
                        break
            
            if is_section_title and section_title:
                if current_section["content"].strip():
                    current_section["end"] = i
                    current_section["line_count"] = i - current_section["start"]
                    sections.append(current_section.copy())
                
                current_section = {
                    "title": section_title.title(),
                    "start": i + 1,
                    "content": ""
                }
            else:
                current_section["content"] += line + "\n"
        
        if current_section["content"].strip():
            current_section["end"] = len(lines)
            current_section["line_count"] = len(lines) - current_section["start"]
            sections.append(current_section)
        
        valid_sections = [s for s in sections if len(s["content"].strip()) > 50]
        return valid_sections
    
    def _extract_keywords(self, text: str, section_title: str = "") -> List[str]:
        """Extraction des mots-clés"""
        keywords = []
        text_lower = text.lower()
        
        domain_keywords = {
            'web': ['html', 'css', 'javascript', 'react', 'vue', 'angular', 'php', 'laravel', 'django', 'flask'],
            'mobile': ['android', 'ios', 'react native', 'flutter', 'kotlin', 'swift'],
            'data': ['python', 'r', 'machine learning', 'data science', 'ai', 'tensorflow', 'pytorch', 'pandas'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'nosql'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'jenkins', 'ci/cd'],
            'general': ['java', 'c++', 'c#', 'python', 'api', 'rest', 'microservices', 'agile', 'scrum']
        }
        
        section_keywords = {
            'formation': ['université', 'école', 'diplôme', 'master', 'licence', 'formation', 'étude'],
            'expérience': ['stage', 'emploi', 'poste', 'entreprise', 'société', 'travail', 'mission'],
            'projets': ['projet', 'développement', 'création', 'réalisation', 'conception', 'implémentation'],
            'compétences': ['compétence', 'maîtrise', 'connaissance', 'expertise', 'skill', 'niveau'],
            'certifications': ['certification', 'diplôme', 'titre', 'qualification', 'accréditation']
        }
        
        # Chercher dans tous les domaines techniques
        for domain, terms in domain_keywords.items():
            for term in terms:
                if term in text_lower:
                    keywords.append(term)
        
        # Chercher les mots-clés spécifiques à la section
        section_lower = section_title.lower()
        for section_key, terms in section_keywords.items():
            if section_key in section_lower:
                for term in terms:
                    if term in text_lower:
                        keywords.append(term)
        
        return list(set(keywords))[:15]
    
    def _identify_chunk_type_from_section(self, section_title: str, text: str) -> str:
        """Identifier le type de chunk basé sur la section"""
        section_lower = section_title.lower()
        
        section_mapping = {
            'formation': 'education',
            'expérience': 'experience', 
            'compétences': 'skills',
            'projets': 'project',
            'certifications': 'certification',
            'contact': 'contact',
            'langues': 'languages',
            'profil': 'profile',
            'objectif': 'objective'
        }
        
        for key, value in section_mapping.items():
            if key in section_lower:
                return value
        
        return self._identify_chunk_type(text)
    
    def _identify_chunk_type(self, text: str) -> str:
        """Identifier le type de contenu du chunk"""
        text_lower = text.lower()
        
        patterns = {
            'education': ['formation', 'diplôme', 'université', 'école', 'master', 'licence', 'baccalauréat', 'étude', 'cursus'],
            'experience': ['stage', 'expérience', 'emploi', 'poste', 'entreprise', 'société', 'travail', 'mission', 'responsabilité'],
            'project': ['projet', 'réalisation', 'développement', 'création', 'conception', 'implémentation', 'application', 'site web'],
            'skills': ['compétence', 'skill', 'maîtrise', 'connaissance', 'expertise', 'niveau', 'langage', 'outil', 'technologie'],
            'certification': ['certification', 'diplôme', 'titre', 'qualification', 'accréditation', 'attestation'],
            'contact': ['contact', 'téléphone', 'email', 'adresse', 'linkedin', 'github', '@', 'mail'],
            'languages': ['langue', 'anglais', 'français', 'espagnol', 'arabe', 'niveau', 'bilingue', 'courant'],
            'personal_info': ['nom', 'âge', 'nationalité', 'situation', 'permis', 'véhicule']
        }
        
        # Compter les correspondances pour chaque type
        type_scores = {}
        for chunk_type, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[chunk_type] = score
        
        # Retourner le type avec le meilleur score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return "general"
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Générer les embeddings par batch - VERSION OPTIMISÉE"""
        try:
            if not texts:
                return []
            
            if not self.executor:
                raise RuntimeError("EmbeddingService non initialisé")
            
            # Nettoyer et valider les textes
            cleaned_texts = []
            for text in texts:
                cleaned = self.text_processor.clean_text(text)
                if cleaned and len(cleaned.strip()) >= 3:
                    cleaned_texts.append(cleaned)
                else:
                    # Ajouter un placeholder pour maintenir l'ordre
                    cleaned_texts.append("contenu vide")
            
            if not cleaned_texts:
                logger.warning("Aucun texte valide après nettoyage")
                return []
            
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor, 
                self._generate_embeddings_sync, 
                cleaned_texts
            )
            
            logger.info(f"✅ Embeddings générés pour {len(cleaned_texts)} textes")
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Erreur génération embeddings batch: {e}")
            raise
    
    def _generate_embeddings_sync(self, texts: List[str]) -> np.ndarray:
        """Version synchrone pour génération par batch"""
        return self.model.encode(texts, convert_to_numpy=True)
    
    # *** RECHERCHE AMÉLIORÉE AVEC ISOLATION STRICTE ***
    async def search_similar_documents(
        self, 
        query: str = None,
        query_embedding: List[float] = None,
        top_k: int = 10,
        threshold: float = 0.1,
        filter_metadata: Dict[str, Any] = None,
        target_person: str = None,  # *** NOUVEAU : Paramètre pour cibler une personne ***
        enable_reranking: bool = True,
        enable_hybrid_search: bool = True
    ) -> List[Dict[str, Any]]:
        
        try:
            logger.info(f"🔍 RECHERCHE AVEC ISOLATION pour: '{query if query else 'embedding direct'}")
            if target_person:
                logger.info(f"🎯 Cible spécifique: {target_person}")
            
            # Vérifier l'état de la collection
            stats = await self.get_collection_stats()
            if stats.get("total_chunks", 0) == 0:
                logger.warning("⚠️ Collection vide !")
                return []
            
            logger.info(f"📊 Collection: {stats['total_chunks']} chunks de {stats['unique_documents']} documents")
            
            # *** NOUVEAU : Construire les filtres d'isolation ***
            isolation_filters = self._build_isolation_filters(filter_metadata, target_person)
            
            # Générer l'embedding de la requête
            if query_embedding is None:
                if not query:
                    logger.error("Ni query ni query_embedding fourni")
                    return []
                
                # Enrichir la requête avec le nom de la personne ciblée si disponible
                enhanced_query = self._enhance_query_with_person(query, target_person)
                logger.info(f"🔧 Requête enrichie: '{enhanced_query}'")
                
                query_embedding = await self.generate_embedding(enhanced_query)
                if not query_embedding:
                    logger.error("Impossible de générer l'embedding pour la requête")
                    return []
            
            # *** RECHERCHE AVEC ISOLATION STRICTE ***
            results = []
            
            # 1. Recherche sémantique avec filtres d'isolation
            try:
                semantic_results = await self._semantic_search_with_isolation(
                    query_embedding, top_k * 2, isolation_filters
                )
                
                for result in semantic_results:
                    result["search_strategy"] = "semantic_isolated"
                
                results.extend(semantic_results)
                logger.info(f"🎯 Recherche sémantique isolée: {len(semantic_results)} résultats")
                
            except Exception as e:
                logger.warning(f"Erreur recherche sémantique isolée: {e}")
            
            # 2. Recherche par mots-clés avec isolation (si activée)
            if enable_hybrid_search and query:
                try:
                    keyword_results = await self._keyword_search_with_isolation(
                        query, target_person, top_k, isolation_filters
                    )
                    
                    for result in keyword_results:
                        result["search_strategy"] = "keyword_isolated"
                    
                    results.extend(keyword_results)
                    logger.info(f"🔤 Recherche mots-clés isolée: {len(keyword_results)} résultats")
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche mots-clés isolée: {e}")
            
            if not results:
                logger.warning("❌ Aucun résultat avec isolation")
                return []
            
            # *** VALIDATION D'ISOLATION POST-RECHERCHE ***
            validated_results = self._validate_isolation(results, target_person)
            logger.info(f"✅ Après validation d'isolation: {len(validated_results)} résultats")
            
            # *** FUSION ET DÉDUPLICATION AVEC VÉRIFICATION D'ISOLATION ***
            merged_results = self._merge_and_deduplicate_isolated_results(validated_results)
            logger.info(f"🔄 Après fusion isolée: {len(merged_results)} résultats uniques")
            
            # *** RE-RANKING AVEC BONUS D'ISOLATION ***
            if enable_reranking and query and merged_results:
                reranked_results = self._rerank_with_isolation_bonus(query, merged_results, target_person)
                logger.info(f"📈 Re-ranking avec bonus d'isolation effectué")
            else:
                reranked_results = merged_results
            
            # *** FILTRAGE FINAL ***
            final_results = [
                result for result in reranked_results 
                if result.get("final_score", result["similarity_score"]) >= threshold
            ][:top_k]
            
            logger.info(f"✅ RECHERCHE ISOLÉE TERMINÉE: {len(final_results)}/{len(results)} résultats finaux")
            
            # Debug des meilleurs résultats avec isolation
            for i, result in enumerate(final_results[:3]):
                person_name = result.get("metadata", {}).get("person_name", "INCONNU")
                logger.debug(f"Result {i+1}: score={result.get('final_score', result['similarity_score']):.3f}, person={person_name}, isolation_valid={result.get('isolation_valid', False)}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche isolée: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _build_isolation_filters(self, filter_metadata: Dict[str, Any], target_person: str = None) -> Dict[str, Any]:
        """*** NOUVEAU : Construire les filtres d'isolation ***"""
        filters = {}
        
        # Ajouter les filtres existants
        if filter_metadata:
            filters.update(filter_metadata)
        
        # *** FILTRE STRICTE PAR PERSONNE ***
        if target_person:
            # Normaliser le nom cible
            target_normalized = re.sub(r'[^a-zA-Z\s]', '', target_person.lower())
            target_normalized = re.sub(r'\s+', '_', target_normalized.strip())
            
            # Utiliser plusieurs stratégies de filtrage
            filters.update({
                "$or": [
                    {"person_name": {"$eq": target_person}},
                    {"person_name_normalized": {"$eq": target_normalized}},
                    {"person_name": {"$regex": f".*{target_person.split()[0]}.*"}},  # Prénom
                    {"isolation_key": {"$regex": f".*{target_normalized}.*"}}
                ]
            })
        
        return filters
    
    def _enhance_query_with_person(self, query: str, target_person: str = None) -> str:
        """*** NOUVEAU : Enrichir la requête avec le nom de la personne ***"""
        if not target_person:
            return query
        
        # Si le nom n'est pas déjà dans la requête, l'ajouter
        if target_person.lower() not in query.lower():
            return f"informations de {target_person} {query}"
        
        return query
    
    async def _semantic_search_with_isolation(
        self, 
        query_embedding: List[float], 
        top_k: int,
        isolation_filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Recherche sémantique avec isolation ***"""
        try:
            # Recherche ChromaDB avec filtres d'isolation
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=isolation_filters if isolation_filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not results.get("documents") or not results["documents"][0]:
                return []
            
            # Formater les résultats
            return self._format_search_results(results)
            
        except Exception as e:
            logger.error(f"Erreur recherche sémantique avec isolation: {e}")
            return []
    
    async def _keyword_search_with_isolation(
        self,
        query: str,
        target_person: str,
        top_k: int,
        isolation_filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Recherche par mots-clés avec isolation ***"""
        try:
            # Extraire les mots-clés de la requête
            query_keywords = self._extract_keywords(query.lower())
            query_words = set(query.lower().split())
            
            # Récupérer les documents avec filtres d'isolation
            all_docs = self.collection.get(
                limit=1000,
                include=["documents", "metadatas"],
                where=isolation_filters if isolation_filters else None
            )
            
            if not all_docs or not all_docs.get("documents"):
                return []
            
            keyword_results = []
            
            # Analyser chaque document avec vérification d'isolation
            for i, (doc, meta) in enumerate(zip(all_docs["documents"], all_docs["metadatas"])):
                # Double vérification d'isolation
                if target_person and not self._is_same_person(meta, target_person):
                    continue
                
                doc_lower = doc.lower()
                meta_keywords = meta.get("keywords", "").lower().split(", ")
                
                # Calculer score de correspondance mots-clés
                keyword_matches = 0
                word_matches = 0
                
                # Correspondances dans les mots-clés
                for kw in query_keywords:
                    if any(kw in meta_kw for meta_kw in meta_keywords):
                        keyword_matches += 2
                    if kw in doc_lower:
                        keyword_matches += 1
                
                # Correspondances dans le contenu
                for word in query_words:
                    if len(word) > 2 and word in doc_lower:
                        word_matches += 1
                
                # Score total
                total_matches = keyword_matches + word_matches
                if total_matches > 0:
                    keyword_score = min(1.0, total_matches / (len(query_keywords) + len(query_words)))
                    
                    keyword_results.append({
                        "content": doc,
                        "similarity_score": keyword_score * 0.8,
                        "distance": 1 - keyword_score,
                        "document_id": meta.get("document_id"),
                        "source_file": meta.get("source_file", meta.get("filename", "Unknown")),
                        "chunk_index": meta.get("chunk_index", 0),
                        "chunk_type": meta.get("chunk_type", "general"),
                        "keywords": meta.get("keywords", ""),
                        "metadata": meta,
                        "keyword_matches": keyword_matches,
                        "word_matches": word_matches,
                        "isolation_valid": True
                    })
            
            # Trier par score et limiter
            keyword_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return keyword_results[:top_k]
            
        except Exception as e:
            logger.error(f"Erreur recherche mots-clés avec isolation: {e}")
            return []
    
    def _is_same_person(self, metadata: Dict[str, Any], target_person: str) -> bool:
        """*** NOUVEAU : Vérifier si les métadonnées correspondent à la personne cible ***"""
        if not target_person:
            return True  # Pas de filtre spécifique
        
        person_name = metadata.get("person_name", "")
        person_name_normalized = metadata.get("person_name_normalized", "")
        
        # Normaliser le nom cible
        target_normalized = re.sub(r'[^a-zA-Z\s]', '', target_person.lower())
        target_normalized = re.sub(r'\s+', '_', target_normalized.strip())
        
        # Vérifications multiples
        checks = [
            person_name.lower() == target_person.lower(),
            person_name_normalized == target_normalized,
            target_person.lower() in person_name.lower(),
            any(part.lower() in person_name.lower() for part in target_person.split() if len(part) > 2)
        ]
        
        return any(checks)
    
    def _validate_isolation(self, results: List[Dict[str, Any]], target_person: str = None) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Valider l'isolation des résultats ***"""
        if not target_person:
            # Marquer tous comme valides si pas de cible spécifique
            for result in results:
                result["isolation_valid"] = True
            return results
        
        validated_results = []
        
        for result in results:
            metadata = result.get("metadata", {})
            is_valid = self._is_same_person(metadata, target_person)
            
            result["isolation_valid"] = is_valid
            
            if is_valid:
                validated_results.append(result)
            else:
                logger.debug(f"❌ Résultat filtré - Personne: {metadata.get('person_name', 'INCONNU')} vs Cible: {target_person}")
        
        return validated_results
    
    def _merge_and_deduplicate_isolated_results(self, all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Fusionner les résultats avec validation d'isolation ***"""
        # Grouper par identifiant unique (document_id + chunk_index + person)
        results_map = {}
        
        for result in all_results:
            person_name = result.get("metadata", {}).get("person_name", "unknown")
            key = f"{result.get('document_id', 'unknown')}_{result.get('chunk_index', 0)}_{person_name}"
            
            if key not in results_map:
                results_map[key] = result
            else:
                # Fusionner les résultats du même chunk de la même personne
                existing = results_map[key]
                
                # Prendre le meilleur score
                if result["similarity_score"] > existing["similarity_score"]:
                    existing["similarity_score"] = result["similarity_score"]
                    existing["primary_strategy"] = result.get("search_strategy", "unknown")
                
                # Combiner les stratégies utilisées
                existing_strategies = existing.get("search_strategies", [existing.get("search_strategy", "")])
                new_strategy = result.get("search_strategy", "")
                
                if new_strategy and new_strategy not in existing_strategies:
                    existing_strategies.append(new_strategy)
                
                existing["search_strategies"] = existing_strategies
                existing["multi_strategy"] = len(existing_strategies) > 1
        
        # Convertir en liste et trier
        merged_results = list(results_map.values())
        merged_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return merged_results
    
    def _rerank_with_isolation_bonus(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        target_person: str = None
    ) -> List[Dict[str, Any]]:
        """*** NOUVEAU : Re-ranking avec bonus d'isolation ***"""
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        query_keywords = set(self._extract_keywords(query_lower))
        
        for result in results:
            content = result.get("content", "").lower()
            metadata = result.get("metadata", {})
            
            # 1. Score de correspondance textuelle
            content_words = set(content.split())
            word_overlap = len(query_words.intersection(content_words))
            word_score = word_overlap / max(len(query_words), 1)
            
            # 2. Score de correspondance mots-clés
            doc_keywords = set(metadata.get("keywords", "").lower().split(", "))
            keyword_overlap = len(query_keywords.intersection(doc_keywords))
            keyword_score = keyword_overlap / max(len(query_keywords), 1) if query_keywords else 0
            
            # 3. Bonus type de chunk
            chunk_type = metadata.get("chunk_type", "general")
            type_bonus = {
                "skills": 0.15,
                "experience": 0.12,
                "project": 0.10,
                "education": 0.08,
                "certification": 0.08,
                "general": 0.0
            }.get(chunk_type, 0.0)
            
            # 4. *** NOUVEAU : Bonus d'isolation stricte ***
            isolation_bonus = 0.0
            if target_person:
                person_name = metadata.get("person_name", "")
                if person_name and target_person.lower() in person_name.lower():
                    isolation_bonus = 0.20  # Bonus important pour la bonne personne
                
                # Bonus supplémentaire si correspondance exacte
                if person_name.lower() == target_person.lower():
                    isolation_bonus += 0.10
            
            # 5. Bonus multi-stratégie
            multi_strategy_bonus = 0.05 if result.get("multi_strategy", False) else 0.0
            
            # 6. Bonus section title
            section_title = metadata.get("section_title", "").lower()
            section_bonus = 0.0
            for word in query_words:
                if word in section_title:
                    section_bonus += 0.03
            
            # 7. Pénalité pour chunks très courts
            content_length = len(result.get("content", ""))
            length_penalty = 0.0
            if content_length < 100:
                length_penalty = -0.05
            elif content_length < 50:
                length_penalty = -0.10
            
            # *** CALCUL DU SCORE FINAL AVEC ISOLATION ***
            base_score = result["similarity_score"]
            
            final_score = (
                base_score * 0.50 +                    # 50% embedding similarity (réduit)
                word_score * 0.15 +                    # 15% word overlap
                keyword_score * 0.10 +                 # 10% keyword overlap
                isolation_bonus +                      # 20-30% bonus d'isolation (NOUVEAU)
                type_bonus +                           # Type bonus
                multi_strategy_bonus +                 # Multi-strategy bonus
                section_bonus +                        # Section relevance bonus
                length_penalty                         # Length penalty
            )
            
            # S'assurer que le score reste dans [0, 1]
            final_score = max(0.0, min(1.0, final_score))
            
            # Stocker les scores détaillés
            result["final_score"] = final_score
            result["scoring_details"] = {
                "base_score": base_score,
                "word_score": word_score,
                "keyword_score": keyword_score,
                "isolation_bonus": isolation_bonus,  # NOUVEAU
                "type_bonus": type_bonus,
                "multi_strategy_bonus": multi_strategy_bonus,
                "section_bonus": section_bonus,
                "length_penalty": length_penalty
            }
        
        # Trier par score final
        results.sort(key=lambda x: x.get("final_score", x["similarity_score"]), reverse=True)
        
        return results
    
    def _format_search_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Formater les résultats de recherche avec isolation"""
        formatted_results = []
        
        if not results or not results.get("documents"):
            return formatted_results
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        
        for doc, meta, distance in zip(documents, metadatas, distances):
            # Meilleure conversion distance -> similarité
            similarity_score = max(0.0, min(1.0, 1.0 - distance))
            
            formatted_results.append({
                "content": doc,
                "similarity_score": similarity_score,
                "distance": distance,
                "document_id": meta.get("document_id"),
                "source_file": meta.get("source_file", meta.get("filename", "Unknown")),
                "chunk_index": meta.get("chunk_index", 0),
                "chunk_type": meta.get("chunk_type", "general"),
                "section_title": meta.get("section_title", ""),
                "keywords": meta.get("keywords", ""),
                "content_preview": meta.get("content_preview", doc[:200] + "..." if len(doc) > 200 else doc),
                "timestamp": meta.get("timestamp"),
                "metadata": meta,
                "person_name": meta.get("person_name", ""),  # NOUVEAU
                "isolation_key": meta.get("isolation_key", "")  # NOUVEAU
            })
        
        return formatted_results
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Statistiques de la collection avec informations d'isolation"""
        try:
            count = self.collection.count()
            
            # Récupérer des échantillons et stats détaillées
            sample_docs = []
            unique_docs = set()
            unique_persons = set()
            chunk_types = {}
            
            if count > 0:
                try:
                    sample_results = self.collection.get(
                        limit=min(100, count), 
                        include=["documents", "metadatas"]
                    )
                    
                    for doc, meta in zip(sample_results["documents"], sample_results["metadatas"]):
                        doc_id = meta.get("document_id")
                        person_name = meta.get("person_name", "")
                        chunk_type = meta.get("chunk_type", "general")
                        
                        unique_docs.add(doc_id)
                        if person_name:
                            unique_persons.add(person_name)
                        
                        # Compter les types de chunks
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                        
                        # Échantillons pour debug
                        if len(sample_docs) < 5:
                            sample_docs.append({
                                "document_id": doc_id,
                                "person_name": person_name,
                                "chunk_index": meta.get("chunk_index"),
                                "chunk_type": chunk_type,
                                "section_title": meta.get("section_title", ""),
                                "content_preview": doc[:150] + "..." if len(doc) > 150 else doc,
                                "timestamp": meta.get("timestamp"),
                                "keywords_count": len(meta.get("keywords", "").split(", ")) if meta.get("keywords") else 0,
                                "isolation_key": meta.get("isolation_key", "")
                            })
                            
                except Exception as e:
                    logger.warning(f"Erreur récupération échantillons: {e}")
            
            return {
                "total_chunks": count,
                "unique_documents": len(unique_docs),
                "unique_persons": len(unique_persons),  # NOUVEAU
                "collection_name": settings.CHROMADB_COLLECTION_NAME,
                "model_name": self.model_name,
                "last_updated": datetime.now().isoformat(),
                "sample_documents": sample_docs,
                "document_ids": sorted(list(unique_docs)),
                "person_names": sorted(list(unique_persons)),  # NOUVEAU
                "chunk_types_distribution": chunk_types,
                "avg_chunks_per_document": round(count / len(unique_docs), 1) if unique_docs else 0,
                "avg_chunks_per_person": round(count / len(unique_persons), 1) if unique_persons else 0  # NOUVEAU
            }
            
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return {
                "error": str(e), 
                "total_chunks": 0,
                "unique_documents": 0,
                "unique_persons": 0,
                "collection_name": settings.CHROMADB_COLLECTION_NAME
            }