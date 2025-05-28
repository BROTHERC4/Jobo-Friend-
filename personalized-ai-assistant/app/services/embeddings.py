from typing import List
import numpy as np
import hashlib
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model with fallback"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}")
            logger.info("Using fallback embedding method")
            self.model = None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with fallback"""
        if self.model is not None:
            try:
                embedding = self.model.encode(text)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"SentenceTransformer encoding failed: {e}")
        
        # Fallback: Simple hash-based embedding
        return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple fallback embedding using text hashing"""
        # Create a simple 384-dimensional embedding (same as all-MiniLM-L6-v2)
        text_hash = hashlib.md5(text.lower().encode()).hexdigest()
        
        # Convert hash to numbers and normalize
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
            embedding.append(value)
        
        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.extend(embedding[:min(len(embedding), 384 - len(embedding))])
        
        embedding = embedding[:384]
        
        # Normalize the vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0 