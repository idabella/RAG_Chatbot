from typing import List, Dict, Any, Optional, AsyncGenerator, TYPE_CHECKING
from datetime import datetime
import asyncio
import logging
import re

from sqlalchemy.orm import Session

from core.config import settings
from services.openrouter_service import OpenRouterService
from utils.text_processing import TextProcessor

# Import conditionnel pour éviter les références circulaires
if TYPE_CHECKING:
    from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:    
    def __init__(self, embedding_service: Optional["EmbeddingService"] = None):
        # Ne pas créer un nouveau service si un est déjà fourni
        if embedding_service is None:
            from services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()
            self._owns_embedding_service = True
        else:
            self.embedding_service = embedding_service
            self._owns_embedding_service = False
        
        # Utilisation d'OpenRouter au lieu d'Ollama
        self.openrouter_service = OpenRouterService()
        self.text_processor = TextProcessor()
        
        # Configuration RAG - SEUILS RÉDUITS
        self.similarity_threshold = getattr(settings, 'RAG_SIMILARITY_THRESHOLD', 0.1)
        self.fallback_threshold = 0.05
        self.max_context_length = getattr(settings, 'RAG_MAX_CONTEXT_LENGTH', 8000)
        self.top_k_documents = getattr(settings, 'RAG_TOP_K_DOCUMENTS', 8)
        
        # NOUVEAU: Prompt système pour réponses claires avec explications
        self.system_prompt = getattr(settings, 'RAG_SYSTEM_PROMPT', 
            "Tu es un assistant IA qui fournit des réponses claires et informatives. "
            "Commence toujours par donner directement l'information demandée, puis ajoute une explication utile. "
            "Sois précis, informatif et utile sans mentionner tes sources de données.")
        
    async def initialize(self):
        """Initialiser les services RAG"""
        try:
            # Initialiser l'embedding service seulement si on le possède
            if self._owns_embedding_service:
                await self.embedding_service.initialize()
            
            # Initialiser OpenRouter
            await self.openrouter_service.initialize()
            
            logger.info("RAG Service initialisé avec OpenRouter/DeepSeek")
            
        except Exception as e:
            logger.error(f"Erreur initialisation RAG Service: {str(e)}")
            raise
        
    async def cleanup(self):
        """Nettoyer les ressources"""
        try:
            if self._owns_embedding_service:
                await self.embedding_service.cleanup()
            
            await self.openrouter_service.cleanup()
            
        except Exception as e:
            logger.warning(f"Erreur cleanup services: {e}")
        
        logger.info("RAG Service nettoyé")

    def _preprocess_query_enhanced(self, query: str) -> str:
        """Préprocessing amélioré avec détection d'intention spécifique"""
        # Corrections orthographiques communes
        corrections = {
            'certifecation': 'certification',
            'certifecations': 'certifications',
            'mustapha': 'Mustapha',
            'idabella': 'Idabella',
            'ces': 'ses',
            'donner moi': 'donne moi',
            'donné moi': 'donne moi',
            'generer': 'générer',
            'numero': 'numéro',
            'ligne': 'ligne téléphone numéro',
            'payment': 'paiement facture',
            'orange': 'Orange opérateur télécom'
        }
        
        processed = query.lower()
        for wrong, correct in corrections.items():
            processed = processed.replace(wrong, correct)
        
        # Détection d'intentions spécifiques pour améliorer la recherche
        if any(word in processed for word in ['numéro', 'ligne', 'téléphone']):
            processed += ' téléphone portable mobile contact'
        
        if any(word in processed for word in ['paiement', 'facture', 'orange']):
            processed += ' facture montant prix abonnement'
        
        logger.info(f"🔧 Query preprocessing: '{query}' -> '{processed}'")
        return processed

    def _extract_direct_answer(self, query: str, context: str) -> Optional[str]:
        """Extraire directement la réponse avec explication si elle est évidente dans le contexte"""
        query_lower = query.lower()
        
        # Recherche de numéro de téléphone
        if any(word in query_lower for word in ['numéro', 'ligne', 'téléphone']):
            phone_patterns = [
                r'0[567]\d{8}',  # Numéros marocains
                r'\d{10}',       # 10 chiffres
                r'\+212\d{9}'    # Format international Maroc
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, context)
                if matches:
                    # Chercher des informations contextuelles
                    context_info = ""
                    if 'orange' in context.lower():
                        context_info += " associé à Orange"
                    if 'paiement' in context.lower():
                        context_info += " dans un fichier de paiement"
                    
                    # Chercher le montant associé
                    amount_match = re.search(r'\d+[,.]?\d*\s*(?:DH|MAD)', context)
                    if amount_match:
                        context_info += f" d'un montant de {amount_match.group()}"
                    
                    return f"Le numéro de ligne est : {matches[0]}\nCette information provient d'un dossier{context_info}."
        
        # Recherche de montant
        if any(word in query_lower for word in ['montant', 'prix', 'coût']):
            amount_patterns = [
                r'\d+[,.]?\d*\s*(?:DH|MAD|€|EUR)',
                r'\d+[,.]?\d*\s*(?:dirhams?|euros?)'
            ]
            
            for pattern in amount_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    context_info = ""
                    if 'paiement' in context.lower():
                        context_info = " pour un paiement effectué"
                    if 'orange' in context.lower():
                        context_info += " chez Orange"
                    
                    return f"Le montant est : {matches[0]}\nIl s'agit du prix{context_info}."
        
        # Recherche de référence
        if any(word in query_lower for word in ['référence', 'ref']):
            ref_patterns = [
                r'[A-Z]-\d{4}-\d{7}',  # Format F-0825-0986083
                r'[A-Z]{1,2}\d{4,}',   # Références alphanumériques
            ]
            
            for pattern in ref_patterns:
                matches = re.findall(pattern, context)
                if matches:
                    context_info = ""
                    if 'paiement' in context.lower():
                        context_info = " de paiement"
                    if 'autorisation' in context.lower():
                        context_info += " utilisée pour l'autorisation de transaction"
                    
                    return f"La référence est : {matches[0]}\nC'est un identifiant{context_info}."
        
        return None
    
    async def generate_response(
        self, 
        query: str,
        user_id: int,
        conversation_id: Optional[int] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Générer une réponse RAG directe et précise"""
        try:
            logger.info(f"Génération de réponse RAG pour user_id={user_id}")
            
            # Préprocesser la requête
            processed_query = self._preprocess_query_enhanced(query)
            logger.info(f"Requête préprocessée: '{processed_query}'")
            
            # Récupérer les documents pertinents
            relevant_docs = await self._retrieve_relevant_documents(
                processed_query, 
                top_k=self.top_k_documents
            )
            
            logger.info(f"Documents trouvés: {len(relevant_docs)}")
            
            # Construire le contexte
            context = await self._build_context(relevant_docs, processed_query)
            
            # NOUVEAU: Essayer d'extraire une réponse directe d'abord
            direct_answer = self._extract_direct_answer(query, context)
            if direct_answer:
                logger.info("✅ Réponse directe extraite")
                return {
                    "response": direct_answer,
                    "sources": [doc["metadata"] for doc in relevant_docs],
                    "confidence": 0.9,  # Confiance élevée pour extraction directe
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_used": len(relevant_docs) > 0,
                    "model_used": "direct_extraction",
                    "extraction_method": "regex_pattern_matching"
                }
            
            if conversation_history is None:
                conversation_history = []
            
            # Construire le prompt optimisé pour des réponses directes
            prompt = await self._build_direct_prompt(
                processed_query, 
                context, 
                conversation_history
            )
            
            # Vérifier que OpenRouter est disponible
            openrouter_health = await self.openrouter_service.health_check()
            if openrouter_health.get("status") != "healthy":
                logger.error("OpenRouter service non disponible")
                return {
                    "response": "Le service de génération de texte est temporairement indisponible.",
                    "sources": [doc["metadata"] for doc in relevant_docs],
                    "confidence": 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_used": len(relevant_docs) > 0,
                    "error": "OpenRouter service unavailable"
                }
            
            # Générer la réponse avec DeepSeek
            logger.info("Génération de la réponse avec OpenRouter/DeepSeek...")
            generated_response = await self.openrouter_service.generate_response(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            # Post-traitement pour nettoyer la réponse
            clean_response = self._clean_response(generated_response)
            
            response_data = {
                "response": clean_response,
                "sources": [doc["metadata"] for doc in relevant_docs],
                "confidence": await self._calculate_confidence(relevant_docs),
                "timestamp": datetime.utcnow().isoformat(),
                "context_used": len(relevant_docs) > 0,
                "model_used": getattr(settings, 'OPENROUTER_MODEL', 'deepseek/deepseek-chat')
            }
            
            logger.info(f"Réponse générée avec succès pour user_id={user_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération RAG: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "response": f"Je rencontre des difficultés techniques pour traiter votre demande.",
                "sources": [],
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "context_used": False,
                "error": str(e)
            }

    def _clean_response(self, response: str) -> str:
        """Nettoyer la réponse pour la rendre plus directe"""
        # Supprimer les mentions de documents et sources
        patterns_to_remove = [
            r'(?:Document \d+[^:]*:?\s*)',
            r'(?:Source[^:]*:?\s*)',
            r'(?:Dans le[^,]*,?\s*)',
            r'(?:Selon le[^,]*,?\s*)',
            r'(?:D\'après[^,]*,?\s*)',
            r'(?:CONCLUSION\s*:?\s*)',
            r'(?:### [^#\n]*\n)',
            r'(?:\*\*[^*]*\*\*\s*:?\s*)',
            r'(?:Cependant[^.]*\.)',
            r'(?:Cette information[^.]*\.)',
        ]
        
        cleaned = response
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Nettoyer les espaces multiples et les sauts de ligne
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Si la réponse est trop courte après nettoyage, retourner l'originale
        if len(cleaned) < 10:
            return response.strip()
        
        return cleaned

    async def _build_direct_prompt(
        self, 
        query: str, 
        context: str, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Construire un prompt optimisé pour des réponses claires avec explications"""
        
        # Historique minimal
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-2:]  # Seulement le dernier échange
            if recent_history:
                history_parts = []
                for msg in recent_history:
                    role = "Q" if msg["role"] == "user" else "R"
                    history_parts.append(f"{role}: {msg['content'][:200]}")
                history_text = f"Contexte récent:\n{chr(10).join(history_parts)}\n\n"
        
        # Prompt pour réponse claire avec explications
        prompt = f"""{history_text}INFORMATIONS DISPONIBLES:
{context}

QUESTION: {query}

INSTRUCTIONS:
- Commence par donner directement l'information demandée
- Ajoute ensuite une explication courte et utile
- Structure ta réponse : RÉPONSE + EXPLICATION
- Ne mentionne pas "Document X" ou tes sources
- Sois précis et informatif
- Si tu ne trouves pas l'information, explique ce qui est disponible à la place

EXEMPLE DE FORMAT:
Le numéro de ligne est : 0657794462
Cette information provient d'un paiement Orange effectué le 29/08/2025 d'un montant de 56,99 DH.

RÉPONSE CLAIRE AVEC EXPLICATION:"""
        
        return prompt
    
    async def generate_response_stream(
        self,
        query: str,
        user_id: int,
        conversation_id: Optional[int] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Version streaming avec réponses directes"""
        try:
            processed_query = self._preprocess_query_enhanced(query)
            relevant_docs = await self._retrieve_relevant_documents(
                processed_query, 
                top_k=self.top_k_documents
            )
            context = await self._build_context(relevant_docs, processed_query)
            
            # Essayer extraction directe d'abord
            direct_answer = self._extract_direct_answer(query, context)
            if direct_answer:
                yield {
                    "type": "metadata",
                    "sources": [doc["metadata"] for doc in relevant_docs],
                    "confidence": 0.9
                }
                yield {
                    "type": "content",
                    "content": direct_answer,
                    "timestamp": datetime.utcnow().isoformat(),
                    "extraction_method": "direct"
                }
                return
            
            if conversation_history is None:
                conversation_history = []
            
            prompt = await self._build_direct_prompt(
                processed_query, 
                context, 
                conversation_history
            )
            
            # Envoyer les métadonnées
            yield {
                "type": "metadata",
                "sources": [doc["metadata"] for doc in relevant_docs],
                "confidence": await self._calculate_confidence(relevant_docs)
            }
            
            # Stream la réponse avec nettoyage
            accumulated_content = ""
            async for chunk in self.openrouter_service.generate_response_stream(
                prompt=prompt,
                system_prompt=self.system_prompt
            ):
                accumulated_content += chunk
                # Nettoyer le contenu accumulé périodiquement
                if len(accumulated_content) > 100:
                    clean_chunk = self._clean_response(accumulated_content)
                    if clean_chunk != accumulated_content:
                        yield {
                            "type": "content_correction",
                            "content": clean_chunk,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        accumulated_content = clean_chunk
                    else:
                        yield {
                            "type": "content",
                            "content": chunk,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                else:
                    yield {
                        "type": "content",
                        "content": chunk,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération RAG en streaming: {str(e)}")
            yield {
                "type": "error", 
                "error": str(e),
                "content": "Erreur technique lors du traitement"
            }
    
    async def _retrieve_relevant_documents(
        self, 
        query: str, 
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """Récupérer les documents pertinents avec debugging simplifié"""
        try:
            logger.info(f"🔍 Recherche pour: '{query}'")
            
            results = await self.embedding_service.search_similar_documents(
                query=query,
                top_k=top_k,
                threshold=0.0
            )
            
            logger.info(f"📊 Résultats bruts: {len(results)}")
            
            # Formater les résultats avec seuils adaptatifs
            relevant_docs = []
            
            # Essayer avec le seuil standard
            for result in results:
                if result.get("similarity_score", 0) >= self.similarity_threshold:
                    doc_data = {
                        "content": result["content"],
                        "similarity_score": result["similarity_score"],
                        "metadata": {
                            "document_id": result.get("document_id"),
                            "source_file": result.get("source_file", "Unknown"),
                            "chunk_index": result.get("chunk_index", 0),
                            "confidence": result["similarity_score"]
                        }
                    }
                    relevant_docs.append(doc_data)
            
            # Fallback si pas assez de résultats
            if len(relevant_docs) < 2 and results:
                logger.info("🔄 Utilisation du seuil de secours")
                relevant_docs = []
                
                for result in results:
                    if result.get("similarity_score", 0) >= self.fallback_threshold:
                        doc_data = {
                            "content": result["content"],
                            "similarity_score": result["similarity_score"],
                            "metadata": {
                                "document_id": result.get("document_id"),
                                "source_file": result.get("source_file", "Unknown"),
                                "chunk_index": result.get("chunk_index", 0),
                                "confidence": result["similarity_score"]
                            }
                        }
                        relevant_docs.append(doc_data)
            
            # Dernier recours: prendre les meilleurs
            if not relevant_docs and results:
                logger.info("🚨 Prise des 2 meilleurs résultats")
                sorted_results = sorted(results, key=lambda x: x.get("similarity_score", 0), reverse=True)
                
                for result in sorted_results[:2]:
                    doc_data = {
                        "content": result["content"],
                        "similarity_score": result["similarity_score"],
                        "metadata": {
                            "document_id": result.get("document_id"),
                            "source_file": result.get("source_file", "Unknown"),
                            "chunk_index": result.get("chunk_index", 0),
                            "confidence": result["similarity_score"]
                        }
                    }
                    relevant_docs.append(doc_data)
            
            logger.info(f"🎯 Documents sélectionnés: {len(relevant_docs)}")
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Erreur recherche documents: {str(e)}")
            return []
    
    async def _build_context(
        self, 
        relevant_docs: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """Construire un contexte concis et pertinent"""
        
        if not relevant_docs:
            return "Aucune information pertinente trouvée."
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(relevant_docs, 1):
            content = doc['content'].strip()
            
            # Format simple sans numérotation excessive
            doc_context = f"{content}\n"
            
            if current_length + len(doc_context) > self.max_context_length:
                break
                
            context_parts.append(doc_context)
            current_length += len(doc_context)
        
        return ''.join(context_parts)
    
    async def _calculate_confidence(self, relevant_docs: List[Dict[str, Any]]) -> float:
        """Calculer le score de confiance simplifié"""
        if not relevant_docs:
            return 0.0
        
        top_similarities = [doc["similarity_score"] for doc in relevant_docs]
        avg_similarity = sum(top_similarities) / len(top_similarities)
        
        # Bonus pour multiple documents
        count_bonus = min(0.1, len(relevant_docs) * 0.02)
        
        confidence = min(1.0, avg_similarity + count_bonus)
        return round(confidence, 2)
    
    # Méthodes utilitaires inchangées...
    async def search_documents(self, query: str, limit: int = 10, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """Rechercher des documents par similarité sémantique"""
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
            
        try:
            processed_query = self._preprocess_query_enhanced(query)
            relevant_docs = await self._retrieve_relevant_documents(processed_query, top_k=limit)
            
            return [
                {
                    "document_id": doc["metadata"]["document_id"],
                    "source_file": doc["metadata"]["source_file"],
                    "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    "similarity_score": doc["similarity_score"],
                    "chunk_index": doc["metadata"]["chunk_index"]
                }
                for doc in relevant_docs
                if doc["similarity_score"] >= similarity_threshold
            ]
            
        except Exception as e:
            logger.error(f"Erreur recherche documents: {str(e)}")
            return []
    
    async def get_conversation_summary(self, conversation_history: List[Dict[str, str]]) -> str:
        """Générer un résumé concis de la conversation"""
        try:
            if not conversation_history:
                return "Aucun historique."
            
            recent_history = conversation_history[-6:]
            conversation_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content'][:150]}" 
                for msg in recent_history
            ])
            
            summary_prompt = f"""Résume cette conversation en 2-3 phrases maximum:

{conversation_text}

Résumé concis:"""
            
            summary = await self.openrouter_service.generate_response(
                prompt=summary_prompt,
                system_prompt="Crée des résumés très concis en français."
            )
            
            return summary.strip()[:300]  # Limiter la longueur
                
        except Exception as e:
            logger.error(f"Erreur génération résumé: {str(e)}")
            return "Résumé indisponible."
    
    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyser l'intention de manière simplifiée"""
        try:
            # Analyse rapide basée sur des mots-clés
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['numéro', 'ligne', 'téléphone']):
                intent_type = "recherche_numero"
                keywords = ['numéro', 'téléphone', 'ligne']
                domain = "telecom"
            elif any(word in query_lower for word in ['montant', 'prix', 'coût', 'facture']):
                intent_type = "recherche_montant"
                keywords = ['montant', 'prix', 'facture']
                domain = "finance"
            elif any(word in query_lower for word in ['référence', 'ref']):
                intent_type = "recherche_reference"
                keywords = ['référence']
                domain = "administratif"
            else:
                intent_type = "general"
                keywords = query_lower.split()[:5]
                domain = "general"
            
            return {
                "type": intent_type,
                "keywords": keywords,
                "domain": domain,
                "complexity": "simple" if len(query.split()) <= 10 else "complexe",
                "confidence": 0.8
            }
                
        except Exception as e:
            return {
                "type": "general",
                "keywords": [],
                "domain": "general",
                "complexity": "moyen",
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérification de santé simplifiée"""
        try:
            openrouter_health = await self.openrouter_service.health_check()
            
            try:
                test_results = await self.embedding_service.search_similar_documents(
                    query="test",
                    top_k=1,
                    threshold=0.0
                )
                embedding_ok = True
            except:
                embedding_ok = False
                test_results = []
            
            return {
                "status": "healthy" if openrouter_health.get("status") == "healthy" and embedding_ok else "degraded",
                "openrouter": openrouter_health.get("status", "unknown"),
                "embedding": "healthy" if embedding_ok else "unhealthy",
                "test_results": len(test_results),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }