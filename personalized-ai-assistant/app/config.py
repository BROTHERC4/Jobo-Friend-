import os
from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = ""
    
    # Database - Railway provides these automatically
    database_url: str = "sqlite:///./jobo.db"  # Fallback for local development
    redis_url: str = "redis://localhost:6379"  # Fallback for local development
    
    # App Settings
    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "production"
    
    # ChromaDB
    chroma_persist_directory: str = "./data/chroma"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Debug environment variables
        logger.info("Environment variables detected:")
        logger.info(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT_SET'}")
        logger.info(f"REDIS_URL: {'SET' if os.getenv('REDIS_URL') else 'NOT_SET'}")
        logger.info(f"REDIS_PRIVATE_URL: {'SET' if os.getenv('REDIS_PRIVATE_URL') else 'NOT_SET'}")
        logger.info(f"REDIS_PUBLIC_URL: {'SET' if os.getenv('REDIS_PUBLIC_URL') else 'NOT_SET'}")
        logger.info(f"ANTHROPIC_API_KEY: {'SET' if os.getenv('ANTHROPIC_API_KEY') else 'NOT_SET'}")
        
        # Use Railway's automatic environment variables with multiple fallbacks
        if os.getenv("DATABASE_URL"):
            self.database_url = os.getenv("DATABASE_URL")
            logger.info(f"Using Railway PostgreSQL: {self.database_url.split('@')[-1] if '@' in self.database_url else 'connected'}")
        else:
            logger.warning("PostgreSQL not detected - using SQLite fallback")
        
        # Check multiple Redis URL formats that Railway might provide
        redis_url = (
            os.getenv("REDIS_URL") or 
            os.getenv("REDIS_PRIVATE_URL") or 
            os.getenv("REDIS_PUBLIC_URL") or
            os.getenv("REDISCLOUD_URL") or
            os.getenv("REDIS_TLS_URL")
        )
        if redis_url:
            self.redis_url = redis_url
            logger.info(f"Using Railway Redis: {redis_url.split('@')[-1] if '@' in redis_url else 'connected'}")
        else:
            logger.warning("Redis not detected - using localhost fallback")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            logger.info("Anthropic API key detected")
        else:
            logger.warning("ANTHROPIC_API_KEY not set - will use fallback responses")
        
        if os.getenv("SECRET_KEY"):
            self.secret_key = os.getenv("SECRET_KEY")
            logger.info("SECRET_KEY detected")
        
        # For development, be less strict about requirements
        if self.environment == "development":
            return
            
        # Validate required settings for production only if not in fallback mode
        if self.environment == "production":
            if not self.anthropic_api_key:
                logger.warning("Warning: ANTHROPIC_API_KEY not set - AI will use fallback responses")
            
            if self.secret_key == "dev-secret-key-change-in-production":
                logger.warning("Warning: SECRET_KEY not set - using development key")

@lru_cache()
def get_settings():
    return Settings() 