from typing import List, Optional, Dict, Any
import numpy as np
import hashlib
import logging
import json
import os
from functools import lru_cache
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class IntelligentEmbeddingService:
    """
    Enhanced embedding service that provides true semantic understanding.
    
    This is the brain upgrade for Jobo - instead of just matching text patterns,
    this service understands the meaning and context of conversations, enabling
    genuine AI intelligence that grows smarter over time.
    """
    
    def __init__(self):
        self.model = None
        self.model_available = False
        self.embedding_cache = {}  # In-memory cache for frequently used embeddings
        self.model_name = getattr(settings, 'embedding_model_name', 'all-MiniLM-L6-v2')
        
        # Initialize the semantic understanding model
        self._initialize_intelligent_model()
        
        # Set up embedding cache if enabled
        cache_size = getattr(settings, 'embedding_cache_size', 1000)
        if cache_size > 0:
            self._setup_embedding_cache()
    
    def _initialize_intelligent_model(self):
        """
        Initialize the semantic understanding model with graceful fallback.
        
        This method attempts to load SentenceTransformers, which gives Jobo
        the ability to understand that "I love programming" and "coding makes me happy"
        are semantically similar, even though they use different words.
        """
        embedding_enabled = getattr(settings, 'embedding_enabled', True)
        if not embedding_enabled:
            logger.info("🧠 Semantic understanding disabled via configuration")
            self.model = None
            self.model_available = False
            return
        
        try:
            logger.info(f"🧠 Loading semantic understanding model: {self.model_name}")
            logger.info("⏳ This may take a moment on first run as the AI brain initializes...")
            
            from sentence_transformers import SentenceTransformer
            
            # Load the semantic understanding model
            # This neural network has been trained on millions of sentences to understand meaning
            self.model = SentenceTransformer(self.model_name)
            self.model_available = True
            
            logger.info(f"✅ Semantic understanding model loaded successfully!")
            logger.info(f"🎯 Model: {self.model_name}")
            logger.info(f"📐 Embedding dimensions: {self.model.get_sentence_embedding_dimension()}")
            
            # Test the model with a simple example
            test_embedding = self.model.encode("Hello world")
            logger.info(f"🧪 Model test successful - generated {len(test_embedding)} dimensional semantic vector")
            
        except ImportError as e:
            logger.warning(f"📦 SentenceTransformers not available: {e}")
            logger.info("💡 To enable semantic understanding, install: pip install sentence-transformers")
            logger.info("🔄 Falling back to pattern-based embedding system")
            self._initialize_fallback_mode()
            
        except Exception as e:
            logger.error(f"❌ Failed to load semantic understanding model: {e}")
            logger.info("🔄 Falling back to pattern-based embedding system")
            self._initialize_fallback_mode()
    
    def _initialize_fallback_mode(self):
        """Initialize the fallback embedding system when semantic understanding isn't available"""
        self.model = None
        self.model_available = False
        logger.info("🔧 Pattern-based embedding system initialized")
        logger.info("💭 Jobo will use structural patterns instead of semantic understanding")
    
    def _setup_embedding_cache(self):
        """Set up intelligent caching for embeddings to improve performance"""
        self.embedding_cache = {}
        cache_size = getattr(settings, 'embedding_cache_size', 1000)
        logger.info(f"🗄️ Embedding cache initialized (size: {cache_size})")
    
    def generate_embedding(self, text: str, cache_key: Optional[str] = None) -> List[float]:
        """
        Generate semantic embedding for text with intelligent caching.
        
        This is where the magic happens - converting human language into mathematical
        vectors that capture meaning and enable intelligent memory retrieval.
        
        Args:
            text: The text to convert into a semantic vector
            cache_key: Optional key for caching (useful for repeated queries)
            
        Returns:
            List of floats representing the semantic meaning of the text
        """
        # Check cache first for performance optimization
        if cache_key and cache_key in self.embedding_cache:
            logger.debug(f"📋 Using cached embedding for: {text[:50]}...")
            return self.embedding_cache[cache_key]
        
        # Generate the embedding using the best available method
        if self.model_available and self.model is not None:
            embedding = self._generate_semantic_embedding(text)
            logger.debug(f"🧠 Generated semantic embedding for: {text[:50]}...")
        else:
            embedding = self._generate_fallback_embedding(text)
            logger.debug(f"🔧 Generated pattern-based embedding for: {text[:50]}...")
        
        # Cache the result if caching is enabled
        cache_size = getattr(settings, 'embedding_cache_size', 1000)
        if cache_key and len(self.embedding_cache) < cache_size:
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def _generate_semantic_embedding(self, text: str) -> List[float]:
        """
        Generate true semantic embedding using SentenceTransformers.
        
        This method uses a neural network trained on millions of sentences to understand
        the actual meaning of text, not just its structural patterns.
        """
        try:
            # Clean and prepare the text
            cleaned_text = self._preprocess_text(text)
            
            # Generate the semantic vector using the neural network
            embedding = self.model.encode(cleaned_text, convert_to_tensor=False)
            
            # Convert to Python list and ensure it's the right type
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            else:
                return embedding.astype(float).tolist()
                
        except Exception as e:
            logger.error(f"❌ Semantic embedding generation failed: {e}")
            logger.info("🔄 Falling back to pattern-based embedding for this text")
            return self._generate_fallback_embedding(text)
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Enhanced pattern-based embedding when semantic understanding isn't available.
        
        This is significantly improved from the basic version - it analyzes text structure,
        patterns, and linguistic features to create meaningful vectors even without
        semantic understanding.
        """
        # Clean and normalize the text
        text = self._preprocess_text(text)
        
        embeddings = []
        
        # Method 1: Enhanced character-based hashing with multiple hash functions
        # This creates a more diverse and representative fingerprint
        for hash_func in [hashlib.md5, hashlib.sha1, hashlib.sha256]:
            char_hash = hash_func(text.encode()).hexdigest()
            for i in range(0, min(len(char_hash), 32), 2):  # Take first 32 chars, step by 2
                hex_pair = char_hash[i:i+2]
                value = int(hex_pair, 16) / 255.0
                embeddings.append(value)
        
        # Method 2: Advanced linguistic features
        words = text.split()
        linguistic_features = self._extract_linguistic_features(text, words)
        embeddings.extend(linguistic_features)
        
        # Method 3: N-gram analysis for context understanding
        ngram_features = self._extract_ngram_features(text)
        embeddings.extend(ngram_features)
        
        # Method 4: Semantic approximation using keyword analysis
        semantic_features = self._extract_semantic_approximation(text, words)
        embeddings.extend(semantic_features)
        
        # Ensure consistent dimensionality (384 dimensions to match sentence-transformers)
        target_size = 384
        embeddings = self._normalize_embedding_size(embeddings, target_size)
        
        # Normalize the vector for consistent similarity calculations
        norm = np.linalg.norm(embeddings)
        if norm > 0:
            embeddings = [x / norm for x in embeddings]
        else:
            # Fallback if norm is 0
            embeddings = [1.0 / target_size] * target_size
        
        return embeddings
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for embedding generation"""
        # Remove excessive whitespace and normalize
        cleaned = ' '.join(text.split())
        
        # Convert to lowercase for consistency
        cleaned = cleaned.lower()
        
        # Remove or replace special characters that don't add semantic value
        import re
        cleaned = re.sub(r'[^\w\s\.\!\?\,\-\:]', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_linguistic_features(self, text: str, words: List[str]) -> List[float]:
        """Extract advanced linguistic features that approximate semantic understanding"""
        features = []
        
        # Basic structural features
        features.extend([
            len(words) / 100.0,  # Word count (normalized)
            sum(len(word) for word in words) / 1000.0,  # Total character count
            len(set(words)) / max(len(words), 1),  # Vocabulary richness
            sum(1 for word in words if len(word) > 6) / max(len(words), 1),  # Complex word ratio
        ])
        
        # Punctuation and style features
        features.extend([
            text.count('?') / max(len(text), 1),  # Question frequency
            text.count('!') / max(len(text), 1),  # Exclamation frequency
            text.count('.') / max(len(text), 1),  # Statement frequency
            sum(1 for c in text if c.isupper()) / max(len(text), 1),  # Emphasis ratio
        ])
        
        # Advanced linguistic patterns
        features.extend([
            sum(1 for word in words if word.startswith(('un', 'dis', 'in', 'im'))) / max(len(words), 1),  # Negative prefixes
            sum(1 for word in words if word.endswith(('ing', 'ed', 'er', 'est'))) / max(len(words), 1),  # Verb/adj forms
            sum(1 for word in words if word in ['i', 'me', 'my', 'myself']) / max(len(words), 1),  # Personal pronouns
            sum(1 for word in words if word in ['you', 'your', 'yourself']) / max(len(words), 1),  # Second person
        ])
        
        return features
    
    def _extract_ngram_features(self, text: str) -> List[float]:
        """Extract n-gram features for context understanding"""
        features = []
        
        # Character-level n-grams (capturing patterns like common endings)
        char_bigrams = [text[i:i+2] for i in range(len(text)-1)]
        char_trigrams = [text[i:i+3] for i in range(len(text)-2)]
        
        # Hash the most common n-grams for consistent representation
        common_bigrams = sorted(set(char_bigrams), key=char_bigrams.count, reverse=True)[:20]
        common_trigrams = sorted(set(char_trigrams), key=char_trigrams.count, reverse=True)[:20]
        
        # Convert to numeric features
        for bigram in common_bigrams[:10]:
            features.append(hash(bigram) % 100 / 100.0)
        
        for trigram in common_trigrams[:10]:
            features.append(hash(trigram) % 100 / 100.0)
        
        return features
    
    def _extract_semantic_approximation(self, text: str, words: List[str]) -> List[float]:
        """Approximate semantic understanding using keyword analysis and topic detection"""
        features = []
        
        # Topic categories for basic semantic understanding
        topics = {
            'technology': ['code', 'programming', 'software', 'computer', 'ai', 'tech', 'api', 'data'],
            'personal': ['feel', 'emotion', 'life', 'family', 'friend', 'love', 'happy', 'sad'],
            'work': ['job', 'career', 'project', 'meeting', 'boss', 'colleague', 'office', 'business'],
            'learning': ['learn', 'study', 'understand', 'teach', 'education', 'knowledge', 'skill'],
            'creative': ['art', 'design', 'creative', 'music', 'write', 'draw', 'create', 'imagine']
        }
        
        # Calculate topic affinity scores
        text_lower = text.lower()
        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            features.append(score / len(keywords))  # Normalized topic score
        
        # Sentiment approximation
        positive_words = ['good', 'great', 'awesome', 'excellent', 'love', 'like', 'happy', 'excited']
        negative_words = ['bad', 'terrible', 'hate', 'dislike', 'sad', 'angry', 'frustrated', 'difficult']
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        features.extend([
            positive_score / len(positive_words),
            negative_score / len(negative_words),
            (positive_score - negative_score) / max(positive_score + negative_score, 1)  # Sentiment balance
        ])
        
        return features
    
    def _normalize_embedding_size(self, embeddings: List[float], target_size: int) -> List[float]:
        """Ensure embedding has consistent size"""
        current_size = len(embeddings)
        
        if current_size == target_size:
            return embeddings
        elif current_size < target_size:
            # Pad with variations of existing values
            while len(embeddings) < target_size:
                for i, val in enumerate(embeddings[:target_size - len(embeddings)]):
                    if len(embeddings) >= target_size:
                        break
                    # Add slight variation to avoid repetition
                    variation = val * (0.9 + 0.2 * ((i % 10) / 10))
                    embeddings.append(variation)
        else:
            # Truncate to target size
            embeddings = embeddings[:target_size]
        
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate semantic similarity between two embeddings using cosine similarity.
        
        Returns a value between -1 and 1, where:
        - 1.0 means the texts are semantically identical
        - 0.0 means they are unrelated
        - -1.0 means they are semantically opposite
        """
        try:
            # Convert to numpy arrays for efficient computation
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure the result is within expected bounds
            return float(np.clip(similarity, -1.0, 1.0))
            
        except Exception as e:
            logger.error(f"❌ Similarity calculation failed: {e}")
            return 0.0
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        This method is optimized for processing multiple texts at once,
        which is more efficient than generating embeddings one by one.
        """
        if not texts:
            return []
        
        if self.model_available and self.model is not None:
            try:
                # Use batch processing for semantic embeddings
                cleaned_texts = [self._preprocess_text(text) for text in texts]
                embeddings = self.model.encode(cleaned_texts, convert_to_tensor=False)
                
                # Convert to list format
                if hasattr(embeddings, 'tolist'):
                    return embeddings.tolist()
                else:
                    return [emb.astype(float).tolist() for emb in embeddings]
                    
            except Exception as e:
                logger.error(f"❌ Batch semantic embedding failed: {e}")
                logger.info("🔄 Falling back to individual embedding generation")
        
        # Fallback to individual processing
        return [self.generate_embedding(text) for text in texts]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model and capabilities"""
        cache_size = getattr(settings, 'embedding_cache_size', 1000)
        return {
            "model_available": self.model_available,
            "model_name": self.model_name if self.model_available else "fallback-pattern-based",
            "embedding_dimensions": 384,  # Standard size we ensure
            "semantic_understanding": self.model_available,
            "cache_enabled": cache_size > 0,
            "cache_size": len(self.embedding_cache),
            "intelligence_level": "semantic" if self.model_available else "pattern-based"
        }

# Create a singleton instance for the application
# This ensures the model is loaded once and reused across requests
@lru_cache()
def get_embedding_service() -> IntelligentEmbeddingService:
    """Get the singleton embedding service instance"""
    return IntelligentEmbeddingService()

# For backward compatibility
EmbeddingService = IntelligentEmbeddingService 