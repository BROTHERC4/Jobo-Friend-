from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.models.database import create_tables
from app.config import get_settings
from app.utils.helpers import setup_logging
import logging
import os

settings = get_settings()

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Jobo AI Assistant...")
    try:
        # Create database tables
        create_tables()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise here to allow app to start even if DB is temporarily unavailable
    
    yield
    
    # Shutdown
    logger.info("Shutting down Jobo AI Assistant...")

app = FastAPI(
    title="Jobo AI Assistant",
    description="A personalized AI assistant that learns and adapts to each user",
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

# Mount static files (with error handling)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Serve the web interface"""
    try:
        return FileResponse("templates/index.html")
    except Exception as e:
        logger.error(f"Could not serve web interface: {e}")
        return {
            "message": "Jobo AI Assistant API",
            "version": "1.0.0",
            "docs": "/docs",
            "description": "A personalized AI assistant that learns from your interactions",
            "note": "Web interface temporarily unavailable",
            "status": "running"
        }

@app.get("/api")
async def api_info():
    return {
        "message": "Jobo AI Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "A personalized AI assistant that learns from your interactions"
    }

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment and status"""
    return {
        "status": "running",
        "service": "Jobo AI Assistant",
        "version": "1.0.0",
        "environment": {
            "PORT": os.getenv("PORT", "Not set"),
            "DATABASE_URL": "Set" if os.getenv("DATABASE_URL") else "Not set",
            "REDIS_URL": "Set" if os.getenv("REDIS_URL") else "Not set", 
            "ANTHROPIC_API_KEY": "Set" if os.getenv("ANTHROPIC_API_KEY") else "Not set",
            "SECRET_KEY": "Set" if os.getenv("SECRET_KEY") else "Not set"
        },
        "endpoints": [
            "/health",
            "/debug", 
            "/api/v1/test",
            "/api/v1/chat",
            "/docs"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    try:
        # Test database connection with proper SQL
        from app.models.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT 1 as test"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "service": "Jobo AI Assistant",
        "database": db_status,
        "version": "1.0.0",
        "message": "Service is running"
    } 