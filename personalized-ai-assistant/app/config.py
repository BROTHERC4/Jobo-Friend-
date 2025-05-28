import os
from pydantic_settings import BaseSettings
from functools import lru_cache

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
        
        # Use Railway's automatic environment variables
        if os.getenv("DATABASE_URL"):
            self.database_url = os.getenv("DATABASE_URL")
        
        # Check multiple Redis URL formats that Railway might provide
        redis_url = (
            os.getenv("REDIS_URL") or 
            os.getenv("REDIS_PRIVATE_URL") or 
            os.getenv("REDIS_PUBLIC_URL")
        )
        if redis_url:
            self.redis_url = redis_url
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if os.getenv("SECRET_KEY"):
            self.secret_key = os.getenv("SECRET_KEY")
        
        # For development, be less strict about requirements
        if self.environment == "development":
            return
            
        # Validate required settings for production only if not in fallback mode
        if self.environment == "production":
            if not self.anthropic_api_key:
                print("Warning: ANTHROPIC_API_KEY not set - AI will use fallback responses")
            
            if self.secret_key == "dev-secret-key-change-in-production":
                print("Warning: SECRET_KEY not set - using development key")

@lru_cache()
def get_settings():
    return Settings() 