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
    ... (full content from embeddings_intelligent.py)
    """
    # ... (rest of the code from embeddings_intelligent.py)

# Create a singleton instance for the application
# This ensures the model is loaded once and reused across requests
@lru_cache()
def get_embedding_service() -> IntelligentEmbeddingService:
    """Get the singleton embedding service instance"""
    return IntelligentEmbeddingService()

# For backward compatibility
EmbeddingService = IntelligentEmbeddingService 