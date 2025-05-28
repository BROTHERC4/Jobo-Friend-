import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
import redis
import json
from app.config import get_settings

settings = get_settings()

class MemoryService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client(ChromaSettings(
            persist_directory=settings.chroma_persist_directory,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(f"user_{user_id}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=f"user_{user_id}",
                metadata={"hnsw:space": "cosine"}
            )
        
        # Initialize Redis
        self.redis_client = redis.from_url(settings.redis_url)
    
    def add_memory(self, text: str, embedding: List[float], metadata: Dict[str, Any]):
        """Add memory to vector database"""
        import hashlib
        memory_id = hashlib.md5(f"{text}{metadata}".encode()).hexdigest()
        
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        return memory_id
    
    def search_memories(self, embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """Search similar memories"""
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=['metadatas', 'documents', 'distances']
        )
        return results
    
    def get_short_term_memory(self) -> List[Dict[str, Any]]:
        """Get recent interactions from Redis"""
        key = f"conversation:{self.user_id}"
        messages = self.redis_client.lrange(key, 0, 9)  # Last 10 messages
        return [json.loads(msg) for msg in messages]
    
    def add_to_short_term_memory(self, message: Dict[str, Any]):
        """Add to short-term memory in Redis"""
        key = f"conversation:{self.user_id}"
        self.redis_client.lpush(key, json.dumps(message))
        self.redis_client.ltrim(key, 0, 49)  # Keep only last 50 messages
        self.redis_client.expire(key, 86400)  # Expire after 24 hours 