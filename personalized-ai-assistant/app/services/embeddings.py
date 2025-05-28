from typing import List
import numpy as np
import hashlib
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_available = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model with fallback"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.model_available = True
            logger.info("SentenceTransformer model loaded successfully")
        except ImportError as e:
            logger.info(f"SentenceTransformers not available: {e}")
            logger.info("Using hash-based fallback embedding method")
            self.model = None
            self.model_available = False
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}")
            logger.info("Using hash-based fallback embedding method")
            self.model = None
            self.model_available = False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with improved fallback"""
        if self.model_available and self.model is not None:
            try:
                embedding = self.model.encode(text)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"SentenceTransformer encoding failed: {e}")
        
        # Use improved hash-based embedding
        return self._improved_hash_embedding(text)
    
    def _improved_hash_embedding(self, text: str) -> List[float]:
        """Improved hash-based embedding that considers text features"""
        # Normalize text
        text = text.lower().strip()
        
        # Create multiple hash values using different methods
        embeddings = []
        
        # Method 1: Character-based hashing
        char_hash = hashlib.md5(text.encode()).hexdigest()
        for i in range(0, len(char_hash), 2):
            hex_pair = char_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0
            embeddings.append(value)
        
        # Method 2: Word-based features
        words = text.split()
        word_features = [
            len(words) / 100.0,  # Number of words (normalized)
            sum(len(word) for word in words) / 1000.0,  # Total character count
            len(set(words)) / max(len(words), 1),  # Unique word ratio
            sum(1 for word in words if len(word) > 5) / max(len(words), 1),  # Long word ratio
        ]
        embeddings.extend(word_features)
        
        # Method 3: Text pattern features
        pattern_features = [
            text.count('?') / max(len(text), 1),  # Question marks
            text.count('!') / max(len(text), 1),  # Exclamation marks
            text.count('.') / max(len(text), 1),  # Periods
            sum(1 for c in text if c.isupper()) / max(len(text), 1),  # Uppercase ratio
        ]
        embeddings.extend(pattern_features)
        
        # Pad or truncate to 384 dimensions (same as all-MiniLM-L6-v2)
        target_size = 384
        while len(embeddings) < target_size:
            # Repeat the embedding with slight variations
            for i, val in enumerate(embeddings[:min(len(embeddings), target_size - len(embeddings))]):
                embeddings.append(val * (0.9 + 0.2 * ((i % 10) / 10)))
        
        embeddings = embeddings[:target_size]
        
        # Normalize the vector
        norm = np.linalg.norm(embeddings)
        if norm > 0:
            embeddings = [x / norm for x in embeddings]
        else:
            # Fallback if norm is 0
            embeddings = [1.0 / target_size] * target_size
        
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0 