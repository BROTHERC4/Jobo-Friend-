from typing import List, Dict, Any
import redis
import json
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MemoryService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.collection = None
        self.redis_client = None
        self.chroma_available = False
        
        # Initialize ChromaDB with error handling
        self._initialize_chromadb()
        
        # Initialize Redis with error handling
        self._initialize_redis()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB with fallback"""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            self.chroma_client = chromadb.Client(ChromaSettings(
                persist_directory=settings.chroma_persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(f"user_{self.user_id}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=f"user_{self.user_id}",
                    metadata={"hnsw:space": "cosine"}
                )
            
            self.chroma_available = True
            logger.info(f"ChromaDB initialized for user {self.user_id}")
            
        except ImportError as e:
            logger.info(f"ChromaDB not available: {e}")
            logger.info("Running without vector memory - basic functionality will work")
            self.collection = None
            self.chroma_available = False
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            logger.info("Running without vector memory - basic functionality will work")
            self.collection = None
            self.chroma_available = False
    
    def _initialize_redis(self):
        """Initialize Redis with fallback"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            logger.info("Running without short-term memory - basic functionality will work")
            self.redis_client = None
    
    def add_memory(self, text: str, embedding: List[float], metadata: Dict[str, Any]):
        """Add memory to vector database"""
        if not self.chroma_available or not self.collection:
            logger.debug("ChromaDB not available, skipping memory storage")
            return self._generate_fallback_id(text, metadata)
        
        try:
            import hashlib
            memory_id = hashlib.md5(f"{text}{metadata}".encode()).hexdigest()
            
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            logger.debug(f"Memory stored in ChromaDB: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return self._generate_fallback_id(text, metadata)
    
    def _generate_fallback_id(self, text: str, metadata: Dict[str, Any]):
        """Generate a fallback memory ID when ChromaDB is not available"""
        import hashlib
        return hashlib.md5(f"{text}{metadata}".encode()).hexdigest()
    
    def search_memories(self, embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """Search similar memories"""
        if not self.chroma_available or not self.collection:
            logger.debug("ChromaDB not available, returning empty results")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=['metadatas', 'documents', 'distances']
            )
            return results
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def get_short_term_memory(self) -> List[Dict[str, Any]]:
        """Get recent interactions from Redis"""
        if not self.redis_client:
            logger.debug("Redis not available, returning empty short-term memory")
            return []
        
        try:
            key = f"conversation:{self.user_id}"
            messages = self.redis_client.lrange(key, 0, 9)  # Last 10 messages
            return [json.loads(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get short-term memory: {e}")
            return []
    
    def add_to_short_term_memory(self, message: Dict[str, Any]):
        """Add to short-term memory in Redis"""
        if not self.redis_client:
            logger.debug("Redis not available, skipping short-term memory storage")
            return
        
        try:
            key = f"conversation:{self.user_id}"
            self.redis_client.lpush(key, json.dumps(message))
            self.redis_client.ltrim(key, 0, 49)  # Keep only last 50 messages
            self.redis_client.expire(key, 86400)  # Expire after 24 hours
        except Exception as e:
            logger.error(f"Failed to add to short-term memory: {e}") 