from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON
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