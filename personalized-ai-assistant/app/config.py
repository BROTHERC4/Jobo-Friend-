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