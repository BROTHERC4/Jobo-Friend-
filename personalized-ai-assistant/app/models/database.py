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