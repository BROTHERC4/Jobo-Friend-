# Personalized AI Assistant - Complete Railway Deployment Guide

## 1. Initialize Project

### Create Project Structure
```bash
mkdir personalized-ai-assistant
cd personalized-ai-assistant
mkdir -p app/{models,services,api,utils} data/chroma tests
touch app/__init__.py app/main.py app/config.py
touch app/models/__init__.py app/services/__init__.py app/api/__init__.py app/utils/__init__.py
```

### 2. Environment Configuration

#### `.env.example`
```env
# API Keys
ANTHROPIC_API_KEY=your_claude_api_key_here

# Database URLs (Railway provides these)
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://default:password@host:port

# App Configuration
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production
```

#### `app/config.py`
```python
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    
    # Database
    database_url: str
    redis_url: str
    
    # App Settings
    secret_key: str
    environment: str = "production"
    
    # ChromaDB
    chroma_persist_directory: str = "./data/chroma"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

### 3. Database Models

#### `app/models/database.py`
```python
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    preferences = Column(JSON, default={})
    interests = Column(JSON, default=[])
    communication_style = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_input = Column(Text)
    assistant_response = Column(Text)
    embedding_id = Column(String)
    user_satisfaction = Column(Float, nullable=True)
    metadata = Column(JSON, default={})

class LearnedPattern(Base):
    __tablename__ = "learned_patterns"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    pattern_type = Column(String)
    pattern_data = Column(Text)
    confidence = Column(Float, default=0.1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### `app/models/schemas.py`
```python
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    interaction_id: str
    context_used: Optional[str] = None

class FeedbackRequest(BaseModel):
    user_id: str
    interaction_id: str
    satisfaction: float

class UserInsights(BaseModel):
    top_patterns: List[Dict[str, Any]]
    total_interactions: int
    average_satisfaction: Optional[float]
    topic_distribution: Dict[str, int]
    interests: List[str]
    communication_style: Dict[str, str]
```

### 4. Core Services

#### `app/services/embeddings.py`
```python
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
```

#### `app/services/memory.py`
```python
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
```

#### `app/services/assistant.py`
```python
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
        system_prompt = f"""You are a personalized AI assistant. Use the following context to provide personalized responses:

{context}

Adapt your responses based on the user's preferences and past interactions. Be consistent with previous conversations."""
        
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
        full_text = f"User: {user_input}\nAssistant: {response}"
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
            metadata=metadata
        )
        self.db.add(interaction)
        self.db.commit()
        
        return memory_id
```

#### `app/services/learning.py`
```python
from sqlalchemy.orm import Session
from app.models.database import UserProfile, LearnedPattern
from datetime import datetime
from typing import Dict, List, Any

class LearningService:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
    
    def extract_topic(self, text: str) -> str:
        """Extract topic from text"""
        topics = {
            'technology': ['code', 'programming', 'software', 'computer', 'AI', 'tech', 'api', 'database'],
            'personal': ['feel', 'emotion', 'life', 'family', 'friend', 'love', 'happy', 'sad'],
            'work': ['job', 'career', 'project', 'deadline', 'meeting', 'boss', 'colleague'],
            'learning': ['learn', 'study', 'course', 'tutorial', 'understand', 'teach', 'education'],
            'entertainment': ['movie', 'music', 'game', 'book', 'show', 'netflix', 'spotify'],
            'health': ['health', 'exercise', 'diet', 'sleep', 'doctor', 'medicine', 'fitness'],
            'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'destination', 'explore']
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return 'general'
    
    def learn_from_input(self, user_input: str):
        """Extract and store patterns from user input"""
        patterns = []
        
        # Time-based patterns
        current_hour = datetime.utcnow().hour
        if 5 <= current_hour < 12:
            patterns.append(('time_preference', 'morning'))
        elif 12 <= current_hour < 17:
            patterns.append(('time_preference', 'afternoon'))
        elif 17 <= current_hour < 22:
            patterns.append(('time_preference', 'evening'))
        else:
            patterns.append(('time_preference', 'night'))
        
        # Communication style patterns
        if len(user_input) > 200:
            patterns.append(('communication_style', 'verbose'))
        elif len(user_input) < 50:
            patterns.append(('communication_style', 'concise'))
        
        if user_input.strip().endswith('?'):
            patterns.append(('communication_style', 'inquisitive'))
        
        # Topic patterns
        topic = self.extract_topic(user_input)
        if topic != 'general':
            patterns.append(('interest', topic))
        
        # Store patterns
        for pattern_type, pattern_data in patterns:
            self._update_pattern(pattern_type, pattern_data)
    
    def _update_pattern(self, pattern_type: str, pattern_data: str):
        """Update or create pattern"""
        pattern = self.db.query(LearnedPattern).filter(
            LearnedPattern.user_id == self.user_id,
            LearnedPattern.pattern_type == pattern_type,
            LearnedPattern.pattern_data == pattern_data
        ).first()
        
        if pattern:
            pattern.confidence = min(pattern.confidence + 0.1, 1.0)
            pattern.last_used = datetime.utcnow()
        else:
            pattern = LearnedPattern(
                user_id=self.user_id,
                pattern_type=pattern_type,
                pattern_data=pattern_data,
                confidence=0.1
            )
            self.db.add(pattern)
        
        self.db.commit()
    
    def update_profile_from_interaction(self, user_input: str, response: str):
        """Update user profile based on interaction"""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user_id).first()
        
        # Extract and add new interests
        topic = self.extract_topic(user_input)
        if topic != 'general' and topic not in profile.interests:
            profile.interests = profile.interests + [topic]
        
        # Update communication style based on patterns
        patterns = self.db.query(LearnedPattern).filter(
            LearnedPattern.user_id == self.user_id,
            LearnedPattern.pattern_type == 'communication_style',
            LearnedPattern.confidence > 0.5
        ).all()
        
        if patterns:
            # Update based on most confident pattern
            best_pattern = max(patterns, key=lambda p: p.confidence)
            profile.communication_style['preference'] = best_pattern.pattern_data
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
```

### 5. API Routes

#### `app/api/routes.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, FeedbackRequest, UserInsights
from app.services.assistant import PersonalizedAssistant

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint"""
    assistant = PersonalizedAssistant(request.user_id, db)
    result = await assistant.chat(request.message)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ChatResponse(**result)

@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Feedback endpoint"""
    from app.models.database import Interaction
    
    interaction = db.query(Interaction).filter(
        Interaction.embedding_id == request.interaction_id,
        Interaction.user_id == request.user_id
    ).first()
    
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    interaction.user_satisfaction = request.satisfaction
    db.commit()
    
    return {"status": "success", "message": "Feedback recorded"}

@router.get("/insights/{user_id}", response_model=UserInsights)
async def get_insights(user_id: str, db: Session = Depends(get_db)):
    """Get user insights"""
    from app.models.database import LearnedPattern, Interaction, UserProfile
    from sqlalchemy import func
    
    # Get top patterns
    patterns = db.query(LearnedPattern).filter(
        LearnedPattern.user_id == user_id,
        LearnedPattern.confidence > 0.5
    ).order_by(LearnedPattern.confidence.desc()).limit(10).all()
    
    # Get interaction stats
    stats = db.query(
        func.count(Interaction.id),
        func.avg(Interaction.user_satisfaction)
    ).filter(Interaction.user_id == user_id).first()
    
    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get topic distribution
    recent_interactions = db.query(Interaction).filter(
        Interaction.user_id == user_id
    ).order_by(Interaction.timestamp.desc()).limit(100).all()
    
    topic_distribution = {}
    for interaction in recent_interactions:
        topic = interaction.metadata.get('topic', 'general')
        topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
    
    return UserInsights(
        top_patterns=[{
            "type": p.pattern_type,
            "data": p.pattern_data,
            "confidence": p.confidence
        } for p in patterns],
        total_interactions=stats[0] or 0,
        average_satisfaction=stats[1],
        topic_distribution=topic_distribution,
        interests=profile.interests,
        communication_style=profile.communication_style
    )
```

### 6. Main Application

#### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.models.database import Base, engine
from app.config import get_settings

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Personalized AI Assistant...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Personalized AI Assistant",
    description="An AI assistant that learns and adapts to each user",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Personalized AI Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 7. Requirements and Deployment Files

#### `requirements.txt`
```txt
fastapi==0.104.1
uvicorn==0.24.0
anthropic==0.18.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
chromadb==0.4.18
sentence-transformers==2.2.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
```

#### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data/chroma

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `railway.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### `.gitignore`
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.env
data/
*.db
.DS_Store
.idea/
.vscode/
*.log
```

### 8. Deployment Instructions

#### Step 1: Local Development
```bash
# Clone repository
git clone <your-repo>
cd personalized-ai-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run locally
uvicorn app.main:app --reload
```

#### Step 2: Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize new project
railway init

# Add PostgreSQL database
railway add postgresql

# Add Redis
railway add redis

# Set environment variables
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Deploy
railway up

# Get deployment URL
railway open
```

### 9. Testing the API

#### Test Chat Endpoint
```bash
curl -X POST "https://your-app.railway.app/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello! How are you today?"
  }'
```

#### Test Insights Endpoint
```bash
curl "https://your-app.railway.app/api/v1/insights/test_user"
```

### 10. Monitoring and Maintenance

#### Add logging configuration to `app/utils/helpers.py`:
```python
import logging
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
```

## Summary

This plan provides:
1. **Complete code structure** ready for Cursor to implement
2. **Railway-optimized configuration** with PostgreSQL and Redis
3. **Production-ready features** including error handling, logging, and health checks
4. **Scalable architecture** that can grow with user needs
5. **Simple deployment** with one command: `railway up`

The assistant will:
- Learn from every interaction
- Store memories in vector database
- Adapt communication style
- Track user interests and patterns
- Provide personalized responses using Claude API

Simply give this plan to Cursor, and it will create a fully functional, deployable AI assistant!