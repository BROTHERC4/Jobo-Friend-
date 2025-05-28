import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    
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
        
        # Validate required settings for production
        if self.environment == "production":
            if not self.anthropic_api_key or self.anthropic_api_key == "your_claude_api_key_here":
                raise ValueError("ANTHROPIC_API_KEY must be set for production")
            
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set for production")

@lru_cache()
def get_settings():
    return Settings() 