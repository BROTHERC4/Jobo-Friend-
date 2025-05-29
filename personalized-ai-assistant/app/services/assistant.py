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
    
    This is the orchestration layer that brings together all the intelligence components
    to create an AI that truly learns, remembers, and grows smarter over time. Instead
    of just responding to individual messages, this assistant builds a comprehensive
    understanding of each user's interests, communication style, and intellectual journey.
    
    Think of this as upgrading from a smart chatbot to a genuine AI companion that
    develops a deep, personalized relationship with each user over time.
    """
    
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        
        # Track intelligence capabilities
        self.intelligence_enabled = is_intelligence_enabled()
        
        # Initialize Claude client with enhanced error handling
        self._initialize_claude_client()
        
        # Initialize intelligence services
        self._initialize_intelligence_services()
        
        # Load or create user profile with enhanced capabilities
        self.user_profile = self._load_or_create_enhanced_profile()
        
        # Log initialization status
        self._log_initialization_status()
    
    def _initialize_claude_client(self):
        """Initialize the Claude API client with robust error handling"""
        try:
            if not settings.anthropic_api_key:
                logger.warning("⚠️ ANTHROPIC_API_KEY not set - using fallback responses")
                self.client = None
                self.claude_available = False
            else:
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self.claude_available = True
                logger.info("✅ Claude API initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude API: {e}")
            self.client = None
            self.claude_available = False
    
    def _initialize_intelligence_services(self):
        """Initialize all intelligence services with graceful fallbacks"""
        # Initialize embedding service for semantic understanding
        try:
            self.embedding_service = get_embedding_service()
            logger.debug("✅ Embedding service connected")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding service: {e}")
            self.embedding_service = None
        
        # Initialize intelligent memory service
        try:
            self.memory_service = IntelligentMemoryService(self.user_id)
            logger.debug("✅ Intelligent memory service connected")
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory service: {e}")
            self.memory_service = None
        
        # Initialize learning service
        try:
            self.learning_service = LearningService(self.user_id, self.db)
            logger.debug("✅ Learning service connected")
        except Exception as e:
            logger.error(f"❌ Failed to initialize learning service: {e}")
            self.learning_service = None
    
    def _load_or_create_enhanced_profile(self) -> UserProfile:
        """Load or create user profile with enhanced intelligence tracking"""
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user_id).first()
            
            if not profile:
                # Create new profile with intelligence-aware defaults
                profile = UserProfile(
                    user_id=self.user_id,
                    name="User",
                    preferences={
                        "intelligence_features_enabled": self.intelligence_enabled,
                        "semantic_understanding": self.embedding_service is not None,
                        "long_term_memory": self.memory_service is not None and getattr(self.memory_service, 'chroma_available', False)
                    },
                    interests=[],
                    communication_style={
                        "formality": "balanced", 
                        "verbosity": "moderate",
                        "learning_style": "adaptive"
                    }
                )
                self.db.add(profile)
                self.db.commit()
                logger.info(f"✨ Created enhanced user profile for {self.user_id}")
            else:
                # Update existing profile with intelligence status
                if not profile.preferences:
                    profile.preferences = {}
                
                profile.preferences.update({
                    "intelligence_features_enabled": self.intelligence_enabled,
                    "semantic_understanding": self.embedding_service is not None,
                    "long_term_memory": self.memory_service is not None and getattr(self.memory_service, 'chroma_available', False)
                })
                self.db.commit()
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Failed to load/create user profile: {e}")
            # Return a default profile that won't cause crashes
            return UserProfile(
                user_id=self.user_id,
                name="User",
                preferences={},
                interests=[],
                communication_style={"formality": "balanced", "verbosity": "moderate"}
            )
    
    def _log_initialization_status(self):
        """Log the initialization status for debugging and monitoring"""
        logger.info(f"🤖 Jobo Intelligence Status for user {self.user_id}:")
        logger.info(f"  Claude API: {'✅ Available' if self.claude_available else '❌ Fallback mode'}")
        logger.info(f"  Semantic Understanding: {'✅ Active' if self.embedding_service else '❌ Disabled'}")
        logger.info(f"  Long-term Memory: {'✅ Active' if self.memory_service and getattr(self.memory_service, 'chroma_available', False) else '❌ Disabled'}")
        logger.info(f"  Short-term Memory: {'✅ Active' if self.memory_service and getattr(self.memory_service, 'redis_client', None) else '❌ Disabled'}")
        logger.info(f"  Learning System: {'✅ Active' if self.learning_service else '❌ Disabled'}")
        logger.info(f"  Overall Intelligence Level: {'🧠 Enhanced' if self.intelligence_enabled else '🔧 Basic'}")
    
    def _build_intelligent_context(self, user_input: str) -> str:
        """
        Build comprehensive context using all available intelligence systems.
        
        This is where the magic happens - instead of just using recent messages,
        we build context from the user's entire history, similar conversations,
        learned patterns, and semantic understanding of their current query.
        """
        context_parts = [
            f"User Profile for {self.user_profile.name}:",
            f"- Communication Style: {self.user_profile.communication_style.get('formality', 'balanced')} formality, {self.user_profile.communication_style.get('verbosity', 'moderate')} verbosity",
            f"- Interests: {', '.join(self.user_profile.interests) if self.user_profile.interests else 'Discovering through conversation'}",
            f"- Intelligence Features: {'Enhanced AI with semantic understanding and long-term memory' if self.intelligence_enabled else 'Standard AI assistant'}",
            ""
        ]
        
        # Add learned patterns with intelligence-based prioritization
        if self.learning_service:
            try:
                # Get patterns with higher confidence thresholds for intelligent mode
                confidence_threshold = 0.4 if self.intelligence_enabled else 0.3
                
                patterns = self.db.query(LearnedPattern).filter(
                    LearnedPattern.user_id == self.user_id,
                    LearnedPattern.confidence > confidence_threshold
                ).order_by(LearnedPattern.confidence.desc()).limit(8).all()
                
                if patterns:
                    context_parts.append("Learned Patterns:")
                    for pattern in patterns:
                        confidence_indicator = "🎯" if pattern.confidence > 0.7 else "📊" if pattern.confidence > 0.5 else "📈"
                        context_parts.append(f"- {confidence_indicator} {pattern.pattern_type}: {pattern.pattern_data} (confidence: {pattern.confidence:.2f})")
                    context_parts.append("")
                    
            except Exception as e:
                logger.warning(f"Could not load learned patterns: {e}")
        
        # Add semantic memory context (the intelligent part)
        if self.memory_service and self.intelligence_enabled:
            try:
                # Search for semantically related memories
                relevant_memories = self.memory_service.search_memories(
                    user_input, 
                    n_results=3,
                    similarity_threshold=0.7
                )
                
                if relevant_memories.get('documents') and relevant_memories['documents'][0]:
                    context_parts.append("Related Past Conversations:")
                    for i, (doc, metadata, similarity) in enumerate(zip(
                        relevant_memories['documents'][0],
                        relevant_memories.get('metadatas', [[]])[0],
                        relevant_memories.get('similarities', [])
                    )):
                        topic = metadata.get('topic', 'general') if metadata else 'general'
                        similarity_pct = f"{similarity * 100:.0f}%" if similarity else "relevant"
                        context_parts.append(f"- {topic.title()} ({similarity_pct} similar): {doc[:120]}...")
                    context_parts.append("")
                    
                # Add short-term conversation context
                recent_messages = self.memory_service.get_short_term_memory(limit=4)
                if recent_messages:
                    context_parts.append("Recent Conversation:")
                    for msg in recent_messages[-3:]:  # Last 3 messages for context
                        role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                        context_parts.append(f"- {role_emoji} {msg['content'][:80]}...")
                    context_parts.append("")
                    
            except Exception as e:
                logger.warning(f"Could not build intelligent context: {e}")
                # Fall back to basic context building
                self._add_basic_memory_context(context_parts, user_input)
        else:
            # Use basic memory context when intelligence isn't available
            self._add_basic_memory_context(context_parts, user_input)
        
        return "\n".join(context_parts)
    
    def _add_basic_memory_context(self, context_parts: List[str], user_input: str):
        """Add basic memory context when intelligent memory isn't available"""
        if self.memory_service:
            try:
                recent_messages = self.memory_service.get_short_term_memory(limit=5)
                if recent_messages:
                    context_parts.append("Recent conversation:")
                    for msg in recent_messages[-3:]:
                        context_parts.append(f"- {msg['role']}: {msg['content'][:100]}...")
                    context_parts.append("")
            except Exception as e:
                logger.debug(f"Could not add basic memory context: {e}")
    
    def _generate_intelligent_system_prompt(self, context: str, user_input: str) -> str:
        """
        Generate an enhanced system prompt that leverages intelligence capabilities.
        
        This prompt is specifically designed to help Claude understand the full
        context and intelligence capabilities available, enabling more sophisticated
        and personalized responses.
        """
        # Define strings separately to avoid backslash issues in f-strings
        learning_awareness = "Show awareness of the user's learning journey and interests over time" if self.intelligence_enabled else "Learn and adapt within the current conversation"
        memory_understanding = "Demonstrate genuine memory and understanding of your relationship with this user" if self.intelligence_enabled else "Be consistent with the patterns you've learned about this user"
        reference_guidance = "Reference relevant past conversations when they add value" if self.intelligence_enabled else "Build on the immediate conversation context"
        value_growth = "grows more valuable with every interaction" if self.intelligence_enabled else "provides consistent, helpful assistance"
        
        base_prompt = f"""You are Jobo, an advanced AI assistant with{'out' if not self.intelligence_enabled else ''} enhanced intelligence capabilities. 

{context}

{'🧠 ENHANCED INTELLIGENCE MODE ACTIVE:' if self.intelligence_enabled else '🔧 STANDARD MODE:'}
{'- You have access to semantic understanding and can make connections between related concepts' if self.intelligence_enabled else '- You are operating with basic pattern matching'}
{'- You can reference and build upon past conversations through long-term memory' if self.intelligence_enabled else '- You have access to recent conversation history only'}
{'- You understand context and meaning, not just keywords' if self.intelligence_enabled else '- You work with direct text matching and learned patterns'}
{'- You can trace intellectual journeys and growth over time' if self.intelligence_enabled else '- You focus on immediate conversation context'}

Communication Guidelines:
- Be conversational, warm, and genuinely helpful
- Adapt your formality and verbosity to match the user's established preferences
- {reference_guidance}
- {learning_awareness}
- Be encouraging and supportive of the user's growth and curiosity
- {memory_understanding}

Your goal is to be a helpful, intelligent companion that {value_growth}."""

        return base_prompt
    
    async def chat(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input with full intelligence capabilities.
        
        This is the main interaction method that orchestrates all the intelligence
        systems to provide the most sophisticated response possible.
        """
        start_time = datetime.utcnow()
        
        # Add to short-term memory for immediate context
        if self.memory_service:
            try:
                self.memory_service.add_to_short_term_memory({
                    "role": "user",
                    "content": user_input,
                    "timestamp": start_time.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to add to short-term memory: {e}")
        
        # Learn from the input (pattern recognition and style analysis)
        if self.learning_service:
            try:
                self.learning_service.learn_from_input(user_input)
            except Exception as e:
                logger.warning(f"Failed to learn from input: {e}")
        
        # Generate response using best available method
        if self.claude_available and self.client:
            response_text = await self._generate_intelligent_response(user_input)
        else:
            response_text = self._get_enhanced_fallback_response(user_input)
        
        # Store the interaction with enhanced metadata
        interaction_id = await self._store_intelligent_interaction(user_input, response_text, start_time)
        
        # Add response to short-term memory
        if self.memory_service:
            try:
                self.memory_service.add_to_short_term_memory({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to add response to short-term memory: {e}")
        
        # Update user profile based on the interaction
        if self.learning_service:
            try:
                self.learning_service.update_profile_from_interaction(user_input, response_text)
            except Exception as e:
                logger.warning(f"Failed to update profile from interaction: {e}")
        
        # Build response with intelligence indicators
        response_data = {
            "response": response_text,
            "interaction_id": interaction_id,
            "intelligence_level": "enhanced" if self.intelligence_enabled else "standard",
            "processing_time": (datetime.utcnow() - start_time).total_seconds()
        }
        
        # Add context summary for debugging/transparency
        if settings.environment == "development":
            context = self._build_intelligent_context(user_input)
            response_data["context_used"] = context[:200] + "..." if len(context) > 200 else context
        
        return response_data
    
    async def _generate_intelligent_response(self, user_input: str) -> str:
        """Generate response using Claude with full intelligence context"""
        try:
            # Build comprehensive context
            context = self._build_intelligent_context(user_input)
            
            # Generate intelligent system prompt
            system_prompt = self._generate_intelligent_system_prompt(context, user_input)
            
            # Call Claude API with enhanced context
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,  # Increased for Claude Sonnet 4's enhanced capabilities
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}]
            )
            
            response_text = message.content[0].text
            logger.info(f"✅ Generated intelligent response using Claude API ({len(response_text)} characters)")
            
            return response_text
            
        except Exception as e:
            logger.error(f"❌ Intelligent Claude API response failed: {e}")
            return self._get_enhanced_fallback_response(user_input)
    
    def _get_enhanced_fallback_response(self, user_input: str) -> str:
        """Generate enhanced fallback response that shows intelligence awareness"""
        # Determine response type with more sophistication
        user_lower = user_input.lower()
        
        # Use learned patterns to inform response if available
        communication_style = "formal" if self.user_profile.communication_style.get('formality') == 'formal' else "friendly"
        user_name = self.user_profile.name if self.user_profile.name != "User" else ""
        
        name_greeting = f", {user_name}" if user_name else ""
        
        if any(word in user_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            if self.intelligence_enabled:
                return f"Hello{name_greeting}! I'm Jobo, your AI assistant with enhanced intelligence capabilities. I can remember our past conversations, understand context and meaning, and learn from our interactions over time. What would you like to explore today?"
            else:
                return f"Hello{name_greeting}! I'm Jobo, your AI assistant. I'm currently in basic mode due to technical limitations, but I'm still here to help you as best I can. What can I assist you with?"
        
        elif user_input.strip().endswith('?') or any(word in user_lower for word in ['what', 'how', 'why', 'when', 'where']):
            if self.intelligence_enabled:
                return f"That's a thoughtful question about '{user_input[:60]}...' I have enhanced capabilities to understand context and draw from our conversation history, but I'm currently experiencing some technical difficulties with my advanced features. I'll give you the best answer I can and make sure to remember this for when my full intelligence comes back online!"
            else:
                return f"I can see you're asking about '{user_input[:60]}...' While I'm in basic mode right now, I'm still working to help you. I'll make note of your question for when my advanced features are restored."
        
        else:
            if self.intelligence_enabled:
                return f"I received your message: '{user_input[:80]}...' I'm designed to understand context, remember our conversations, and learn from our interactions, but I'm currently experiencing some technical issues with my advanced features. I'm still here and engaged with what you're sharing!"
            else:
                return f"Thanks for your message: '{user_input[:80]}...' I'm currently in basic mode, but I'm still here to help and learn from our conversation."
    
    async def _store_intelligent_interaction(self, user_input: str, response: str, start_time: datetime) -> str:
        """Store interaction with enhanced metadata and semantic memory"""
        try:
            # Generate comprehensive metadata
            metadata = {
                "timestamp": start_time.isoformat(),
                "intelligence_enabled": self.intelligence_enabled,
                "semantic_understanding": self.embedding_service is not None,
                "response_length": len(response),
                "processing_method": "claude_api" if self.claude_available else "fallback"
            }
            
            # Add topic analysis if learning service available
            if self.learning_service:
                try:
                    topic = self.learning_service.extract_topic(user_input)
                    metadata["topic"] = topic
                    metadata["user_input_preview"] = user_input[:100]
                except Exception:
                    metadata["topic"] = "general"
            
            # Store in semantic memory if available
            memory_id = f"interaction_{start_time.strftime('%Y%m%d_%H%M%S')}"
            
            if self.memory_service and self.intelligence_enabled:
                try:
                    # Create full conversation text for semantic storage
                    full_conversation = f"User: {user_input}\n\nJobo: {response}"
                    
                    # Store in semantic memory system
                    memory_id = self.memory_service.add_memory(
                        text=full_conversation,
                        metadata=metadata
                    )
                    logger.debug(f"💾 Stored interaction in semantic memory: {memory_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to store in semantic memory: {e}")
            
            # Store in PostgreSQL database
            interaction = Interaction(
                user_id=self.user_id,
                user_input=user_input,
                assistant_response=response,
                embedding_id=memory_id,
                interaction_metadata=metadata
            )
            self.db.add(interaction)
            self.db.commit()
            
            logger.debug(f"📊 Stored interaction in database")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store intelligent interaction: {e}")
            return "error_storing_interaction"
    
    def get_intelligence_status(self) -> Dict[str, Any]:
        """Get detailed status of intelligence capabilities for this user"""
        status = {
            "user_id": self.user_id,
            "intelligence_enabled": self.intelligence_enabled,
            "claude_api_available": self.claude_available,
            "components": {
                "semantic_understanding": {
                    "available": self.embedding_service is not None,
                    "model_info": self.embedding_service.get_model_info() if self.embedding_service else None
                },
                "long_term_memory": {
                    "available": self.memory_service is not None and getattr(self.memory_service, 'chroma_available', False),
                    "statistics": self.memory_service.get_memory_statistics() if self.memory_service else None
                },
                "short_term_memory": {
                    "available": self.memory_service is not None and getattr(self.memory_service, 'redis_client', None) is not None
                },
                "learning_system": {
                    "available": self.learning_service is not None
                }
            },
            "user_profile": {
                "name": self.user_profile.name,
                "interests_count": len(self.user_profile.interests) if self.user_profile.interests else 0,
                "communication_style": self.user_profile.communication_style,
                "preferences": self.user_profile.preferences
            }
        }
        
        return status

# For backward compatibility
PersonalizedAssistant = IntelligentPersonalizedAssistant 