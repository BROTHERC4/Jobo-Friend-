from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.models.database import Base, engine
from app.config import get_settings
from app.utils.helpers import setup_logging

settings = get_settings()

# Setup logging
logger = setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Jobo AI Assistant...")
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Serve the web interface"""
    return FileResponse("templates/index.html")

@app.get("/api")
async def api_info():
    return {
        "message": "Jobo AI Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "A personalized AI assistant that learns from your interactions"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Jobo AI Assistant"} 