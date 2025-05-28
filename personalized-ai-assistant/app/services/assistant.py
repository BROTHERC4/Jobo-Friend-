import anthropic
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.database import UserProfile, Interaction, LearnedPattern
from app.services.embeddings import EmbeddingService
from app.services.memory import MemoryService
from app.services.learning import LearningService
from app.config import get_settings

settings = get_settings()

class PersonalizedAssistant:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.embedding_service = EmbeddingService()
        self.memory_service = MemoryService(user_id)
        self.learning_service = LearningService(user_id, db)
        self.user_profile = self._load_or_create_profile()
    
    def _load_or_create_profile(self) -> UserProfile:
        """Load or create user profile"""
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
    
    def _build_context(self, user_input: str) -> str:
        """Build personalized context from memories and profile"""
        # Generate embedding for current input
        input_embedding = self.embedding_service.generate_embedding(user_input)
        
        # Search similar memories
        similar_memories = self.memory_service.search_memories(input_embedding, n_results=5)
        
        # Get short-term memory
        recent_messages = self.memory_service.get_short_term_memory()
        
        # Build context
        context_parts = [
            f"User Profile:",
            f"- Name: {self.user_profile.name}",
            f"- Interests: {', '.join(self.user_profile.interests) if self.user_profile.interests else 'Not specified'}",
            f"- Communication Style: {self.user_profile.communication_style.get('formality', 'balanced')} formality",
            ""
        ]
        
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages[-3:]:
                context_parts.append(f"- {msg['role']}: {msg['content'][:100]}...")
            context_parts.append("")
        
        if similar_memories['documents']:
            context_parts.append("Relevant past interactions:")
            for doc, metadata in zip(similar_memories['documents'][0][:3], similar_memories['metadatas'][0][:3]):
                context_parts.append(f"- {metadata.get('topic', 'general')}: {doc[:100]}...")
        
        return "\n".join(context_parts)
    
    async def chat(self, user_input: str) -> Dict[str, Any]:
        """Process user input and generate response"""
        # Add to short-term memory
        self.memory_service.add_to_short_term_memory({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Build context
        context = self._build_context(user_input)
        
        # Learn from input
        self.learning_service.learn_from_input(user_input)
        
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
            
            # Add response to short-term memory
            self.memory_service.add_to_short_term_memory({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update profile
            self.learning_service.update_profile_from_interaction(user_input, response_text)
            
            return {
                "response": response_text,
                "interaction_id": interaction_id,
                "context_used": context[:200] + "..." if len(context) > 200 else context
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, I encountered an error. Please try again.",
                "interaction_id": None,
                "error": str(e)
            }
    
    def _store_interaction(self, user_input: str, response: str) -> str:
        """Store interaction in database and vector store"""
        # Generate embedding for the interaction
        full_text = f"User: {user_input}\nJobo: {response}"
        embedding = self.embedding_service.generate_embedding(full_text)
        
        # Extract topic
        topic = self.learning_service.extract_topic(user_input)
        
        # Store in vector database
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "topic": topic,
            "user_input": user_input[:200]
        }
        memory_id = self.memory_service.add_memory(full_text, embedding, metadata)
        
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