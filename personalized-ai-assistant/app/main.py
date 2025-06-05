from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.api.auth import router as auth_router
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
        # Create database tables (including new authentication tables)
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
    description="A personalized AI assistant with secure authentication that learns and adapts to each user",
    version="2.0.0",
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
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("Static files mounted successfully")
    else:
        logger.warning("Static directory not found")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(router, prefix="/api/v1", tags=["AI Assistant"])

# Include enhanced capabilities routes
try:
    logger.info("🔄 Attempting to load enhanced AI capabilities...")
    from app.api.enhanced_routes import get_enhanced_router
    logger.info("✅ Enhanced routes module imported successfully")
    
    enhanced_router = get_enhanced_router()
    logger.info("✅ Enhanced router created successfully")
    logger.info(f"📋 Enhanced router has {len(enhanced_router.routes)} routes")
    
    # Log individual routes for debugging
    for route in enhanced_router.routes:
        logger.info(f"📍 Route: {route.path} ({route.methods})")
    
    app.include_router(enhanced_router, prefix="/api/v1/enhanced", tags=["Enhanced AI"])
    logger.info("✅ Enhanced AI capabilities loaded successfully")
    
    # Verify routes were actually added to the app
    enhanced_routes_count = len([route for route in app.routes if "/enhanced" in str(route.path)])
    logger.info(f"🔍 Total enhanced routes registered in app: {enhanced_routes_count}")
    
except ImportError as e:
    logger.error(f"❌ Import error loading enhanced AI capabilities: {e}")
    import traceback
    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    logger.info("Running with basic AI features only")
except Exception as e:
    logger.error(f"❌ Error loading enhanced AI capabilities: {e}")
    import traceback
    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    logger.info("Running with basic AI features only")

@app.get("/ping")
async def ping():
    """Simple ping endpoint to test if app is responding"""
    return {"status": "pong", "message": "Jobo AI Assistant is responding"}

@app.get("/")
async def root():
    """Serve the web interface"""
    try:
        if os.path.exists("templates/index.html"):
            return FileResponse("templates/index.html")
        else:
            logger.warning("index.html not found, serving basic response")
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Jobo AI Assistant</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; text-align: center; }
                    .status { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
                    .auth-notice { background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }
                    .links { text-align: center; margin: 30px 0; }
                    .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                    .links a:hover { background: #0056b3; }
                    .auth-links a { background: #28a745; }
                    .auth-links a:hover { background: #1e7e34; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 Jobo AI Assistant v2.0</h1>
                    <div class="status">
                        <h3>✅ Service Status: Running with Authentication</h3>
                        <p>Your personalized AI assistant is up and running with secure user accounts!</p>
                    </div>
                    <div class="auth-notice">
                        <h3>🔐 New in v2.0: User Authentication</h3>
                        <p>Create an account to enjoy personalized AI conversations with secure data protection.</p>
                        <ul>
                            <li>✅ Secure user registration and login</li>
                            <li>✅ Personal AI learning and memory</li>
                            <li>✅ Protected conversation history</li>
                            <li>✅ Backward compatibility with legacy endpoints</li>
                        </ul>
                    </div>
                    <div class="links auth-links">
                        <a href="/docs#/Authentication/register">🆕 Register Account</a>
                        <a href="/docs#/Authentication/login">🔑 Login</a>
                    </div>
                    <div class="links">
                        <a href="/docs">📚 API Documentation</a>
                        <a href="/api/v1/test">🧪 Test API</a>
                        <a href="/health">❤️ Health Check</a>
                        <a href="/debug">🔧 Debug Info</a>
                    </div>
                    <p style="text-align: center; color: #666;">
                        A personalized AI assistant that learns and adapts to each user
                    </p>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Could not serve web interface: {e}")
        return {
            "message": "Jobo AI Assistant API",
            "version": "2.0.0",
            "features": ["Authentication", "Personalized AI", "Secure Data"],
            "docs": "/docs",
            "description": "A personalized AI assistant that learns from your interactions",
            "note": "Web interface temporarily unavailable",
            "status": "running"
        }

@app.get("/api")
async def api_info():
    return {
        "message": "Jobo AI Assistant API",
        "version": "2.0.0",
        "features": ["Authentication", "Personalized AI", "Secure Data"],
        "docs": "/docs",
        "description": "A personalized AI assistant that learns from your interactions",
        "authentication": {
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "logout": "/api/v1/auth/logout",
            "profile": "/api/v1/auth/me"
        },
        "endpoints": {
            "authenticated": {
                "chat": "/api/v1/chat",
                "feedback": "/api/v1/feedback", 
                "insights": "/api/v1/insights"
            },
            "enhanced": {
                "vision_analysis": "/api/v1/enhanced/vision/analyze",
                "daily_insights": "/api/v1/enhanced/insights/daily",
                "pattern_analysis": "/api/v1/enhanced/insights/patterns",
                "memory_optimization": "/api/v1/enhanced/memory/consolidate",
                "memory_clusters": "/api/v1/enhanced/memory/clusters",
                "conversation_summary": "/api/v1/enhanced/conversation/summarize",
                "intelligence_status": "/api/v1/enhanced/intelligence/status"
            },
            "legacy": {
                "chat": "/api/v1/legacy/chat",
                "feedback": "/api/v1/legacy/feedback",
                "insights": "/api/v1/legacy/insights/{user_id}"
            }
        }
    }

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment and status"""
    return {
        "status": "running",
        "service": "Jobo AI Assistant",
        "version": "2.0.0",
        "features": ["Authentication", "Personalized AI", "Secure Data"],
        "environment": {
            "PORT": os.getenv("PORT", "Not set"),
            "DATABASE_URL": "Set" if os.getenv("DATABASE_URL") else "Not set",
            "REDIS_URL": "Set" if os.getenv("REDIS_URL") else "Not set", 
            "ANTHROPIC_API_KEY": "Set" if os.getenv("ANTHROPIC_API_KEY") else "Not set",
            "SECRET_KEY": "Set" if os.getenv("SECRET_KEY") else "Not set"
        },
        "file_system": {
            "templates_exists": os.path.exists("templates"),
            "static_exists": os.path.exists("static"),
            "index_html_exists": os.path.exists("templates/index.html"),
            "current_directory": os.getcwd(),
            "directory_contents": os.listdir(".")
        },
        "endpoints": {
            "core": ["/health", "/debug", "/api/v1/test"],
            "authentication": [
                "/api/v1/auth/register",
                "/api/v1/auth/login", 
                "/api/v1/auth/logout",
                "/api/v1/auth/me"
            ],
            "ai_assistant": [
                "/api/v1/chat",
                "/api/v1/feedback", 
                "/api/v1/insights"
            ],
            "enhanced": [
                route.path for route in app.routes 
                if hasattr(route, 'path') and "/enhanced" in str(route.path)
            ],
            "legacy": [
                "/api/v1/legacy/chat",
                "/api/v1/legacy/feedback",
                "/api/v1/legacy/insights/{user_id}"
            ]
        },
        "route_debug": {
            "total_routes": len(app.routes),
            "enhanced_routes_detected": len([
                route for route in app.routes 
                if hasattr(route, 'path') and "/enhanced" in str(route.path)
            ])
        }
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
        "version": "2.0.0",
        "features": ["Authentication", "Personalized AI", "Secure Data"],
        "message": "Service is running"
    } 