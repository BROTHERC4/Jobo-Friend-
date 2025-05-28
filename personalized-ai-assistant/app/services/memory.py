from typing import List, Dict, Any, Optional, Tuple
import redis
import json
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class IntelligentMemoryService:
    """
    Enhanced memory service that provides semantic understanding and long-term memory.
    
    This service creates a two-tier memory system:
    1. Short-term memory (Redis) - Recent conversation context
    2. Long-term semantic memory (ChromaDB) - Searchable by meaning, not just keywords
    
    This enables Jobo to remember and understand conversations over time, making
    connections between related topics even when discussed weeks apart.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.collection = None
        self.redis_client = None
        self.chroma_available = False
        self.chroma_client = None
        
        # Initialize semantic memory (ChromaDB) with graceful fallback
        self._initialize_semantic_memory()
        
        # Initialize short-term memory (Redis) with graceful fallback
        self._initialize_short_term_memory()
        
        # Log memory system status
        self._log_memory_status()
    
    def _initialize_semantic_memory(self):
        """
        Initialize ChromaDB for semantic long-term memory.
        
        This creates a vector database that can understand meaning and context,
        allowing Jobo to find related conversations even when different words are used.
        """
        chroma_enabled = getattr(settings, 'chroma_enabled', True)
        if not chroma_enabled:
            logger.info("🧠 Semantic memory disabled via configuration")
            self.chroma_available = False
            return
        
        try:
            logger.info(f"🧠 Initializing semantic memory for user {self.user_id}")
            
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # Initialize ChromaDB client with persistence
            persist_dir = getattr(settings, 'chroma_persist_directory', './data/chroma')
            
            self.chroma_client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create user-specific collection
            collection_name = f"user_{self.user_id}_memories"
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                logger.debug(f"📚 Loaded existing memory collection: {collection_name}")
            except Exception:
                # Create new collection with optimized settings
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": "cosine",  # Use cosine similarity for semantic search
                        "hnsw:construction_ef": 200,  # Higher quality index
                        "hnsw:M": 16  # Good balance of speed and accuracy
                    }
                )
                logger.info(f"✨ Created new memory collection: {collection_name}")
            
            self.chroma_available = True
            logger.info(f"✅ Semantic memory initialized successfully")
            
            # Get collection statistics
            try:
                count = self.collection.count()
                logger.info(f"📊 Memory collection contains {count} stored memories")
            except Exception:
                logger.debug("Could not get memory count")
            
        except ImportError as e:
            logger.warning(f"📦 ChromaDB not available: {e}")
            logger.info("💡 To enable semantic memory, install: pip install chromadb")
            logger.info("🔄 Running with basic memory only")
            self._initialize_fallback_semantic_memory()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize semantic memory: {e}")
            logger.info("🔄 Running with basic memory only")
            self._initialize_fallback_semantic_memory()
    
    def _initialize_fallback_semantic_memory(self):
        """Initialize fallback when ChromaDB isn't available"""
        self.collection = None
        self.chroma_available = False
        self.chroma_client = None
        logger.info("🔧 Semantic memory fallback initialized")
    
    def _initialize_short_term_memory(self):
        """
        Initialize Redis for short-term conversational memory.
        
        This stores recent conversation context that can be quickly accessed
        to maintain conversation flow and immediate context awareness.
        """
        try:
            logger.info("🧠 Initializing short-term memory (Redis)")
            
            # Connect to Redis with connection pooling
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test the connection
            self.redis_client.ping()
            logger.info("✅ Short-term memory (Redis) connected successfully")
            
            # Set up memory expiration policies
            self._setup_memory_expiration()
            
        except Exception as e:
            logger.warning(f"❌ Redis connection failed: {e}")
            logger.info("🔄 Running without short-term memory - conversations won't persist between sessions")
            self.redis_client = None
    
    def _setup_memory_expiration(self):
        """Set up automatic expiration for memory management"""
        if not self.redis_client:
            return
        
        try:
            # Set default expiration for conversation keys
            conversation_key = f"conversation:{self.user_id}"
            if self.redis_client.exists(conversation_key):
                self.redis_client.expire(conversation_key, 86400)  # 24 hours
                
            # Set expiration for session data
            session_key = f"session:{self.user_id}"
            if self.redis_client.exists(session_key):
                self.redis_client.expire(session_key, 3600)  # 1 hour
                
        except Exception as e:
            logger.debug(f"Could not set memory expiration: {e}")
    
    def _log_memory_status(self):
        """Log the memory system initialization status"""
        logger.info(f"🧠 Memory System Status for user {self.user_id}:")
        logger.info(f"  Semantic Memory (ChromaDB): {'✅ Active' if self.chroma_available else '❌ Disabled'}")
        logger.info(f"  Short-term Memory (Redis): {'✅ Active' if self.redis_client else '❌ Disabled'}")
        
        if self.chroma_available:
            try:
                count = self.collection.count()
                logger.info(f"  Stored Memories: {count}")
            except Exception:
                logger.info(f"  Stored Memories: Unknown")
    
    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a memory to the semantic memory system.
        
        This method stores conversations in a way that enables semantic search,
        meaning Jobo can find related conversations based on meaning, not just keywords.
        
        Args:
            text: The conversation text to store
            metadata: Additional context about the memory
            
        Returns:
            Memory ID for reference
        """
        if metadata is None:
            metadata = {}
        
        # Add timestamp and user context
        enhanced_metadata = {
            **metadata,
            "user_id": self.user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": len(text),
            "memory_type": "conversation"
        }
        
        # Generate unique memory ID
        memory_id = f"mem_{self.user_id}_{uuid.uuid4().hex[:12]}"
        
        if self.chroma_available and self.collection:
            try:
                # Get embedding service for semantic storage
                from app.services.embeddings import get_embedding_service
                embedding_service = get_embedding_service()
                
                # Generate semantic embedding
                embedding = embedding_service.generate_embedding(text, cache_key=f"memory_{memory_id}")
                
                # Store in semantic memory
                self.collection.add(
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[enhanced_metadata],
                    ids=[memory_id]
                )
                
                logger.debug(f"💾 Stored semantic memory: {memory_id}")
                return memory_id
                
            except Exception as e:
                logger.error(f"❌ Failed to store semantic memory: {e}")
                return self._store_fallback_memory(text, enhanced_metadata, memory_id)
        else:
            return self._store_fallback_memory(text, enhanced_metadata, memory_id)
    
    def _store_fallback_memory(self, text: str, metadata: Dict[str, Any], memory_id: str) -> str:
        """Store memory when semantic storage isn't available"""
        if self.redis_client:
            try:
                # Store in Redis as fallback
                fallback_key = f"fallback_memory:{self.user_id}:{memory_id}"
                memory_data = {
                    "text": text,
                    "metadata": metadata,
                    "id": memory_id
                }
                self.redis_client.setex(fallback_key, 604800, json.dumps(memory_data))  # 7 days
                logger.debug(f"💾 Stored fallback memory in Redis: {memory_id}")
            except Exception as e:
                logger.warning(f"Failed to store fallback memory: {e}")
        
        return memory_id
    
    def search_memories(self, query: str, n_results: int = 5, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Search memories using semantic understanding.
        
        This is the intelligent part - instead of just matching keywords,
        this searches for memories that are semantically related to the query.
        
        Args:
            query: What to search for
            n_results: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            Dictionary with documents, metadata, and similarity scores
        """
        if not self.chroma_available or not self.collection:
            logger.debug("Semantic search not available, returning empty results")
            return self._search_fallback_memories(query, n_results)
        
        try:
            # Get embedding service for semantic search
            from app.services.embeddings import get_embedding_service
            embedding_service = get_embedding_service()
            
            # Generate query embedding
            query_embedding = embedding_service.generate_embedding(query, cache_key=f"search_{hashlib.md5(query.encode()).hexdigest()[:8]}")
            
            # Search semantic memory
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 20),  # Cap at 20 for performance
                include=['metadatas', 'documents', 'distances']
            )
            
            # Filter by similarity threshold and convert distances to similarities
            filtered_results = self._filter_and_convert_results(results, similarity_threshold)
            
            logger.debug(f"🔍 Semantic search found {len(filtered_results.get('documents', [[]])[0])} relevant memories")
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return self._search_fallback_memories(query, n_results)
    
    def _filter_and_convert_results(self, results: Dict[str, Any], similarity_threshold: float) -> Dict[str, Any]:
        """Filter results by similarity threshold and convert distances to similarities"""
        if not results.get('distances') or not results['distances'][0]:
            return {"documents": [[]], "metadatas": [[]], "similarities": []}
        
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        # Convert distances to similarities (ChromaDB uses cosine distance)
        similarities = [1.0 - distance for distance in distances]
        
        # Filter by threshold
        filtered_docs = []
        filtered_metas = []
        filtered_sims = []
        
        for doc, meta, sim in zip(documents, metadatas, similarities):
            if sim >= similarity_threshold:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                filtered_sims.append(sim)
        
        return {
            "documents": [filtered_docs],
            "metadatas": [filtered_metas],
            "similarities": filtered_sims
        }
    
    def _search_fallback_memories(self, query: str, n_results: int) -> Dict[str, Any]:
        """Search memories when semantic search isn't available"""
        if not self.redis_client:
            return {"documents": [[]], "metadatas": [[]], "similarities": []}
        
        try:
            # Simple keyword-based search in Redis fallback memories
            pattern = f"fallback_memory:{self.user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            matching_memories = []
            query_lower = query.lower()
            
            for key in keys[:50]:  # Limit search scope
                try:
                    memory_data = json.loads(self.redis_client.get(key))
                    text = memory_data.get('text', '').lower()
                    
                    # Simple keyword matching
                    if any(word in text for word in query_lower.split()):
                        matching_memories.append(memory_data)
                        
                except Exception:
                    continue
            
            # Sort by relevance (simple word count matching)
            matching_memories.sort(
                key=lambda x: sum(word in x.get('text', '').lower() for word in query_lower.split()),
                reverse=True
            )
            
            # Format results
            results = matching_memories[:n_results]
            return {
                "documents": [[mem.get('text', '') for mem in results]],
                "metadatas": [[mem.get('metadata', {}) for mem in results]],
                "similarities": [0.5] * len(results)  # Default similarity for keyword matches
            }
            
        except Exception as e:
            logger.error(f"Fallback memory search failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "similarities": []}
    
    def get_short_term_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation messages from short-term memory.
        
        This provides immediate context for the current conversation session.
        
        Args:
            limit: Maximum number of recent messages to retrieve
            
        Returns:
            List of recent conversation messages
        """
        if not self.redis_client:
            logger.debug("Short-term memory not available")
            return []
        
        try:
            conversation_key = f"conversation:{self.user_id}"
            messages = self.redis_client.lrange(conversation_key, 0, limit - 1)
            
            # Parse and return messages in chronological order
            parsed_messages = []
            for msg in reversed(messages):  # Reverse to get chronological order
                try:
                    parsed_messages.append(json.loads(msg))
                except json.JSONDecodeError:
                    continue
            
            logger.debug(f"📋 Retrieved {len(parsed_messages)} recent messages")
            return parsed_messages
            
        except Exception as e:
            logger.error(f"❌ Failed to get short-term memory: {e}")
            return []
    
    def add_to_short_term_memory(self, message: Dict[str, Any]):
        """
        Add a message to short-term conversational memory.
        
        This maintains the immediate conversation context that helps Jobo
        understand the current discussion flow.
        
        Args:
            message: Message data to store (should include role, content, timestamp)
        """
        if not self.redis_client:
            logger.debug("Short-term memory not available, skipping storage")
            return
        
        try:
            conversation_key = f"conversation:{self.user_id}"
            
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()
            
            # Store message
            self.redis_client.lpush(conversation_key, json.dumps(message))
            
            # Maintain conversation length (keep last 100 messages)
            self.redis_client.ltrim(conversation_key, 0, 99)
            
            # Set expiration
            self.redis_client.expire(conversation_key, 86400)  # 24 hours
            
            logger.debug(f"💬 Added message to short-term memory")
            
        except Exception as e:
            logger.error(f"❌ Failed to add to short-term memory: {e}")
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the memory system for this user"""
        stats = {
            "user_id": self.user_id,
            "semantic_memory_available": self.chroma_available,
            "short_term_memory_available": self.redis_client is not None,
            "semantic_memory_count": 0,
            "short_term_memory_count": 0,
            "memory_system_health": "unknown"
        }
        
        # Get semantic memory statistics
        if self.chroma_available and self.collection:
            try:
                stats["semantic_memory_count"] = self.collection.count()
            except Exception as e:
                logger.debug(f"Could not get semantic memory count: {e}")
        
        # Get short-term memory statistics
        if self.redis_client:
            try:
                conversation_key = f"conversation:{self.user_id}"
                stats["short_term_memory_count"] = self.redis_client.llen(conversation_key)
            except Exception as e:
                logger.debug(f"Could not get short-term memory count: {e}")
        
        # Determine overall health
        if self.chroma_available and self.redis_client:
            stats["memory_system_health"] = "excellent"
        elif self.chroma_available or self.redis_client:
            stats["memory_system_health"] = "partial"
        else:
            stats["memory_system_health"] = "basic"
        
        return stats
    
    def clear_short_term_memory(self):
        """Clear the short-term conversation memory"""
        if not self.redis_client:
            return
        
        try:
            conversation_key = f"conversation:{self.user_id}"
            self.redis_client.delete(conversation_key)
            logger.info(f"🧹 Cleared short-term memory for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to clear short-term memory: {e}")

# For backward compatibility
MemoryService = IntelligentMemoryService 