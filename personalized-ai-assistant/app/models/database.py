from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Create engine with better error handling
try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database connected successfully to: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'local'}")
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    raise

Base = declarative_base()

# Authentication Tables
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    user_id = Column(String, unique=True, index=True, nullable=False)  # Links to existing system
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SessionToken(Base):
    __tablename__ = "session_tokens"
    
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)  # Links to User.user_id
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Existing AI System Tables (preserved exactly as they were)
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
    interaction_metadata = Column(JSON, default={})  # Renamed from 'metadata' to avoid conflict

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

# Create tables with error handling
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise 