import anthropic
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.database import UserProfile, Interaction, LearnedPattern
from app.services.embeddings import get_embedding_service
from app.services.memory import IntelligentMemoryService
from app.services.learning import LearningService
from app.config import get_settings, is_intelligence_enabled
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()

class IntelligentPersonalizedAssistant:
    """
    Enhanced AI assistant with semantic understanding and long-term memory.
    ... (full content from assistant_intelligent.py)
    """
    # ... (rest of the code from assistant_intelligent.py)

# For backward compatibility
PersonalizedAssistant = IntelligentPersonalizedAssistant

class PersonalizedAssistant:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        
        # Initialize Claude client with error handling
        try:
            if not settings.anthropic_api_key:
                logger.warning("ANTHROPIC_API_KEY not set - using fallback responses")
                self.client = None
                self.claude_available = False
            else:
                # Use the correct Anthropic client initialization for latest version
                self.client = anthropic.Anthropic(
                    api_key=settings.anthropic_api_key
                )
                self.claude_available = True
                logger.info("Claude API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude API: {e}")
            self.client = None
            self.claude_available = False
        
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
                logger.info(f"Created new user profile for {self.user_id}")
            
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
            f"- Interests: {', '.join(self.user_profile.interests) if self.user_profile.interests else 'General topics'}",
            f"- Communication Style: {self.user_profile.communication_style.get('formality', 'balanced')} formality",
            f"- Preferred Verbosity: {self.user_profile.communication_style.get('verbosity', 'moderate')}",
            ""
        ]
        
        # Add learned patterns if available
        if self.learning_service:
            try:
                patterns = self.db.query(LearnedPattern).filter(
                    LearnedPattern.user_id == self.user_id,
                    LearnedPattern.confidence > 0.3
                ).order_by(LearnedPattern.confidence.desc()).limit(5).all()
                
                if patterns:
                    context_parts.append("User Patterns:")
                    for pattern in patterns:
                        context_parts.append(f"- {pattern.pattern_type}: {pattern.pattern_data} (confidence: {pattern.confidence:.1f})")
                    context_parts.append("")
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
        
        # Try to get memory context if services are available
        if self.embedding_service and self.memory_service:
            try:
                # Generate embedding for current input
                input_embedding = self.embedding_service.generate_embedding(user_input)
                
                # Search similar memories
                similar_memories = self.memory_service.search_memories(input_embedding, n_results=3)
                
                # Get short-term memory
                recent_messages = self.memory_service.get_short_term_memory()
                
                if recent_messages:
                    context_parts.append("Recent conversation:")
                    for msg in recent_messages[-3:]:
                        context_parts.append(f"- {msg['role']}: {msg['content'][:100]}...")
                    context_parts.append("")
                
                if similar_memories['documents'] and similar_memories['documents'][0]:
                    context_parts.append("Relevant past interactions:")
                    for doc, metadata in zip(similar_memories['documents'][0][:2], similar_memories['metadatas'][0][:2]):
                        context_parts.append(f"- {metadata.get('topic', 'general')}: {doc[:100]}...")
                    context_parts.append("")
            except Exception as e:
                logger.warning(f"Failed to build memory context: {e}")
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Generate a fallback response when Claude API is not available"""
        responses = {
            'greeting': [
                "Hello! I'm Jobo, your AI assistant. I'm currently in basic mode due to a technical issue, but I'm working!",
                "Hi there! I'm Jobo. While I'm having some connectivity issues with my advanced features, I'm still here to help!",
                "Hey! Jobo here. I'm running in simplified mode right now, but I'm happy to chat with you!"
            ],
            'question': [
                f"That's an interesting question about '{user_input[:50]}...'. I'm currently in basic mode, but I'd love to help you explore this topic once my full capabilities are restored!",
                f"I can see you're curious about '{user_input[:50]}...'. While I'm in simplified mode, I'm noting your interest for when my advanced features come back online!",
                f"Great question! I'm storing your query about '{user_input[:50]}...' and will give you a comprehensive answer once I'm fully operational again."
            ],
            'general': [
                f"I received your message: '{user_input[:100]}...'. I'm currently in basic mode due to a technical issue, but I'm working!",
                f"Thanks for sharing that with me! I'm in simplified mode right now, but I'm learning from our conversation.",
                f"I appreciate you talking with me! While my advanced features are temporarily limited, I'm still here and listening."
            ]
        }
        
        # Determine response type
        user_lower = user_input.lower()
        if any(word in user_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            response_type = 'greeting'
        elif user_input.strip().endswith('?') or any(word in user_lower for word in ['what', 'how', 'why', 'when', 'where']):
            response_type = 'question'
        else:
            response_type = 'general'
        
        import random
        return random.choice(responses[response_type])
    
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
        
        # Learn from input if available
        if self.learning_service:
            try:
                self.learning_service.learn_from_input(user_input)
            except Exception as e:
                logger.warning(f"Failed to learn from input: {e}")
        
        # Try Claude API first, fallback to basic response
        if self.claude_available and self.client:
            try:
                # Build context
                context = self._build_context(user_input)
                
                # Generate enhanced system prompt
                system_prompt = f"""You are Jobo, a friendly and personalized AI assistant. Use the following context to provide personalized responses:

{context}

Guidelines:
- Be conversational and friendly
- Adapt your formality level based on the user's communication style
- Reference past conversations when relevant
- Show genuine interest in the user's topics
- Be helpful and informative
- Keep responses engaging but not overly long
- Remember you're learning about this user over time

Respond naturally as Jobo, incorporating the personalization context above."""
                
                # Call Claude API
                message = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_input}]
                )
                
                response_text = message.content[0].text
                logger.info("Generated response using Claude API")
                
            except Exception as e:
                logger.error(f"Claude API failed: {e}")
                response_text = self._get_fallback_response(user_input)
                logger.info("Used fallback response")
        else:
            response_text = self._get_fallback_response(user_input)
            logger.info("Used fallback response (Claude not available)")
        
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
            "context_used": self._build_context(user_input)[:200] + "..." if len(self._build_context(user_input)) > 200 else self._build_context(user_input)
        }
    
    def _store_interaction(self, user_input: str, response: str) -> str:
        """Store interaction in database and vector store"""
        try:
            # Generate embedding for the interaction if service is available
            memory_id = f"interaction_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
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
                    logger.debug(f"Stored interaction in vector database: {memory_id}")
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
            logger.debug(f"Stored interaction in PostgreSQL")
            
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
            return "error_storing_interaction" 