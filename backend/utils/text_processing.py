from typing import List, Dict, Any, Optional
import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class TextProcessor:    
    def __init__(self):
        self.stop_words_fr = {
            'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour',
            'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus',
            'par', 'grand', 'en', 'une', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je', 'son',
            'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'de', 'le', 'un', 'à'
        }
        
        self.stop_words_en = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
    
    def clean_text(self, text: str, aggressive: bool = True) -> str:
        if not text or not isinstance(text, str):
            return ""
        
        text = text.strip()
        
        if aggressive:
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
            text = re.sub(r'\.{2,}', '.', text)
            text = re.sub(r'\!{2,}', '!', text)
            text = re.sub(r'\?{2,}', '?', text)
        
        return text.strip()

    @lru_cache(maxsize=1000)
    def detect_language(self, text: str) -> Optional[str]:
        if not text or len(text.strip()) < 10:
            return None
        
        try:
            from langdetect import detect
            return detect(self.clean_text(text, aggressive=False))
        except Exception:
            french_words = len([word for word in text.lower().split() if word in self.stop_words_fr])
            english_words = len([word for word in text.lower().split() if word in self.stop_words_en])
            
            if french_words > english_words:
                return 'fr'
            elif english_words > 0:
                return 'en'
            else:
                return 'fr'
    
    def tokenize_words(self, text: str, language: str = 'fr') -> List[str]:
        if not text:
            return []
        
        clean_text = self.clean_text(text)
        
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', clean_text.lower())
        
        stop_words = self.stop_words_fr if language == 'fr' else self.stop_words_en
        tokens = [word for word in words if word not in stop_words and len(word) >= 2]
        
        return tokens
    
    def tokenize_sentences(self, text: str, language: str = 'fr') -> List[str]:
        if not text:
            return []
        
        clean_text = self.clean_text(text)
        
        sentences = re.split(r'[.!?]+', clean_text)
        sentences = [sent.strip() for sent in sentences if sent.strip() and len(sent.strip()) > 5]
        
        return sentences
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        if not text:
            return []
        
        language = self.detect_language(text) or 'fr'
        words = self.tokenize_words(text, language)
        
        word_freq = {}
        for word in words:
            if len(word) >= 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        sentences = self.tokenize_sentences(text)
        
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                    if len(current_chunk) > overlap:
                        overlap_text = current_chunk[-overlap:]
                        current_chunk = overlap_text + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    if len(sentence) > chunk_size:
                        words = sentence.split()
                        temp_chunk = ""
                        for word in words:
                            if len(temp_chunk) + len(word) + 1 > chunk_size:
                                if temp_chunk:
                                    chunks.append(temp_chunk.strip())
                                temp_chunk = word
                            else:
                                temp_chunk += " " + word if temp_chunk else word
                        current_chunk = temp_chunk
                    else:
                        current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                'char_count': 0,
                'word_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'language': None,
                'avg_word_length': 0,
                'avg_sentence_length': 0
            }
        
        language = self.detect_language(text)
        words = self.tokenize_words(text, language or 'fr')
        sentences = self.tokenize_sentences(text, language or 'fr')
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'language': language,
            'avg_word_length': round(sum(len(word) for word in words) / len(words), 2) if words else 0,
            'avg_sentence_length': round(len(words) / len(sentences), 2) if sentences else 0
        }
    
    def preprocess_for_embedding(self, text: str) -> str:
        if not text:
            return ""
        
        text = self.clean_text(text, aggressive=True)
        language = self.detect_language(text) or 'fr'
        
        text = re.sub(r'\d+', '[NUM]', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_entities_simple(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        
        entities = []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            entities.append({
                'text': email,
                'label': 'EMAIL',
                'confidence': 0.9
            })
        
        phone_pattern = r'\b(?:\+33|0)[1-9](?:[0-9]{8})\b'
        phones = re.findall(phone_pattern, text)
        for phone in phones:
            entities.append({
                'text': phone,
                'label': 'PHONE',
                'confidence': 0.8
            })
        
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            entities.append({
                'text': url,
                'label': 'URL',
                'confidence': 0.9
            })
        
        return entities
    
    def similarity_score(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        words1 = set(self.tokenize_words(text1))
        words2 = set(self.tokenize_words(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_summary(self, text: str, max_sentences: int = 3) -> str:
        if not text:
            return ""
        
        sentences = self.tokenize_sentences(text)
        
        if len(sentences) <= max_sentences:
            return text
        
        sentence_scores = {}
        words = self.tokenize_words(text)
        word_freq = {}
        
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        for i, sentence in enumerate(sentences):
            sentence_words = self.tokenize_words(sentence)
            score = sum(word_freq.get(word, 0) for word in sentence_words)
            sentence_scores[i] = score / len(sentence_words) if sentence_words else 0
        
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sentences.sort(key=lambda x: x[0])
        
        summary_sentences = [sentences[i] for i, _ in top_sentences]
        
        return '. '.join(summary_sentences) + '.'


_text_processor = None

def get_text_processor() -> TextProcessor:
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor

def clean_text(text: str, aggressive: bool = True) -> str:
    return get_text_processor().clean_text(text, aggressive)

def detect_language(text: str) -> Optional[str]:
    return get_text_processor().detect_language(text)

def tokenize_for_embedding(text: str) -> List[str]:
    processor = get_text_processor()
    language = processor.detect_language(text) or 'fr'
    return processor.tokenize_words(text, language)

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    return get_text_processor().chunk_text(text, chunk_size, overlap)

def preprocess_for_embedding(text: str) -> str:
    return get_text_processor().preprocess_for_embedding(text)

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    return get_text_processor().extract_keywords(text, max_keywords)

def get_text_stats(text: str) -> Dict[str, Any]:
    return get_text_processor().get_text_stats(text)

