import anthropic
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.database import UserProfile, Interaction, LearnedPattern
from app.services.embeddings import EmbeddingService
from app.services.memory import MemoryService
from app.services.learning import LearningService
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class PersonalizedAssistant:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        
        # Initialize services with error handling
        try:
            self.embedding_service = EmbeddingService()
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            self.embedding_service = None
        
        try:
            self.memory_service = MemoryService(user_id)
        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            self.memory_service = None
        
        try:
            self.learning_service = LearningService(user_id, db)
        except Exception as e:
            logger.error(f"Failed to initialize learning service: {e}")
            self.learning_service = None
        
        self.user_profile = self._load_or_create_profile()
    
    def _load_or_create_profile(self) -> UserProfile:
        """Load or create user profile"""
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user_id).first()
            
            if not profile:
                profile = UserProfile(
                    user_id=self.user_id,
                    name="User",
                    preferences={},
                    interests=[],
                    communication_style={"formality": "balanced", "verbosity": "moderate"}
                )
                self.db.add(profile)
                self.db.commit()
            
            return profile
        except Exception as e:
            logger.error(f"Failed to load/create user profile: {e}")
            # Return a default profile
            return UserProfile(
                user_id=self.user_id,
                name="User",
                preferences={},
                interests=[],
                communication_style={"formality": "balanced", "verbosity": "moderate"}
            )
    
    def _build_context(self, user_input: str) -> str:
        """Build personalized context from memories and profile"""
        context_parts = [
            f"User Profile:",
            f"- Name: {self.user_profile.name}",
            f"- Interests: {', '.join(self.user_profile.interests) if self.user_profile.interests else 'Not specified'}",
            f"- Communication Style: {self.user_profile.communication_style.get('formality', 'balanced')} formality",
            ""
        ]
        
        # Try to get memory context if services are available
        if self.embedding_service and self.memory_service:
            try:
                # Generate embedding for current input
                input_embedding = self.embedding_service.generate_embedding(user_input)
                
                # Search similar memories
                similar_memories = self.memory_service.search_memories(input_embedding, n_results=5)
                
                # Get short-term memory
                recent_messages = self.memory_service.get_short_term_memory()
                
                if recent_messages:
                    context_parts.append("Recent conversation:")
                    for msg in recent_messages[-3:]:
                        context_parts.append(f"- {msg['role']}: {msg['content'][:100]}...")
                    context_parts.append("")
                
                if similar_memories['documents'] and similar_memories['documents'][0]:
                    context_parts.append("Relevant past interactions:")
                    for doc, metadata in zip(similar_memories['documents'][0][:3], similar_memories['metadatas'][0][:3]):
                        context_parts.append(f"- {metadata.get('topic', 'general')}: {doc[:100]}...")
            except Exception as e:
                logger.warning(f"Failed to build memory context: {e}")
        
        return "\n".join(context_parts)
    
    async def chat(self, user_input: str) -> Dict[str, Any]:
        """Process user input and generate response"""
        # Add to short-term memory if available
        if self.memory_service:
            try:
                self.memory_service.add_to_short_term_memory({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to add to short-term memory: {e}")
        
        # Build context
        context = self._build_context(user_input)
        
        # Learn from input if available
        if self.learning_service:
            try:
                self.learning_service.learn_from_input(user_input)
            except Exception as e:
                logger.warning(f"Failed to learn from input: {e}")
        
        # Generate system prompt
        system_prompt = f"""You are Jobo, a personalized AI assistant. Use the following context to provide personalized responses:

{context}

Adapt your responses based on the user's preferences and past interactions. Be consistent with previous conversations. You are friendly, helpful, and remember what users tell you."""
        
        try:
            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}]
            )
            
            response_text = message.content[0].text
            
            # Store interaction
            interaction_id = self._store_interaction(user_input, response_text)
            
            # Add response to short-term memory if available
            if self.memory_service:
                try:
                    self.memory_service.add_to_short_term_memory({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to add response to short-term memory: {e}")
            
            # Update profile if available
            if self.learning_service:
                try:
                    self.learning_service.update_profile_from_interaction(user_input, response_text)
                except Exception as e:
                    logger.warning(f"Failed to update profile: {e}")
            
            return {
                "response": response_text,
                "interaction_id": interaction_id,
                "context_used": context[:200] + "..." if len(context) > 200 else context
            }
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            return {
                "response": f"I apologize, I encountered an error. Please try again.",
                "interaction_id": None,
                "error": str(e)
            }
    
    def _store_interaction(self, user_input: str, response: str) -> str:
        """Store interaction in database and vector store"""
        try:
            # Generate embedding for the interaction if service is available
            memory_id = "basic_interaction_id"
            metadata = {
                "timestamp": datetime.utcnow().isoformat(),
                "topic": "general",
                "user_input": user_input[:200]
            }
            
            if self.embedding_service and self.memory_service and self.learning_service:
                try:
                    full_text = f"User: {user_input}\nJobo: {response}"
                    embedding = self.embedding_service.generate_embedding(full_text)
                    
                    # Extract topic
                    topic = self.learning_service.extract_topic(user_input)
                    metadata["topic"] = topic
                    
                    # Store in vector database
                    memory_id = self.memory_service.add_memory(full_text, embedding, metadata)
                except Exception as e:
                    logger.warning(f"Failed to store in vector database: {e}")
            
            # Store in PostgreSQL
            interaction = Interaction(
                user_id=self.user_id,
                user_input=user_input,
                assistant_response=response,
                embedding_id=memory_id,
                interaction_metadata=metadata
            )
            self.db.add(interaction)
            self.db.commit()
            
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
            return "error_storing_interaction" 