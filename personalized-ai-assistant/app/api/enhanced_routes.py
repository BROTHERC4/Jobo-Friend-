from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging

from app.models.database import get_db
from app.api.auth import get_current_user_id

# Lazy imports to avoid import-time errors
def get_vision_service():
    try:
        from app.services.vision_service import get_vision_service as _get_vision_service
        return _get_vision_service()
    except Exception as e:
        logger.error(f"Failed to import vision service: {e}")
        raise

def get_proactive_service(user_id: str, db):
    try:
        from app.services.proactive_service import get_proactive_service as _get_proactive_service
        return _get_proactive_service(user_id, db)
    except Exception as e:
        logger.error(f"Failed to import proactive service: {e}")
        raise

def get_memory_consolidation_service(user_id: str):
    try:
        from app.services.memory_enhancement import get_memory_consolidation_service as _get_memory_consolidation_service
        return _get_memory_consolidation_service(user_id)
    except Exception as e:
        logger.error(f"Failed to import memory consolidation service: {e}")
        raise

def get_intelligent_memory_service(user_id: str):
    try:
        from app.services.memory import IntelligentMemoryService
        return IntelligentMemoryService(user_id)
    except Exception as e:
        logger.error(f"Failed to import memory service: {e}")
        raise

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.get("/test")
async def test_enhanced_routes():
    """Simple test endpoint to verify enhanced routes are loading"""
    return {
        "success": True,
        "message": "Enhanced routes are working!",
        "routes": [
            "/vision/analyze",
            "/insights/daily", 
            "/insights/patterns",
            "/memory/consolidate",
            "/memory/clusters",
            "/memory/stats",
            "/conversation/summarize",
            "/intelligence/status"
        ]
    }

@router.post("/vision/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = "Analyze this image in detail",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Analyze an uploaded image using Claude's vision capabilities.
    
    This endpoint enables users to upload images for AI analysis,
    including screenshots, documents, charts, photos, etc.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Analyze image with error handling for service availability
        try:
            vision_service = get_vision_service()
            analysis = vision_service.analyze_image(image_data, prompt)
        except Exception as service_error:
            logger.error(f"Vision service error: {service_error}")
            return {
                "success": False,
                "error": "Vision service temporarily unavailable",
                "message": "Image analysis service is currently not available. Please try again later.",
                "debug_info": str(service_error) if logger.getEffectiveLevel() <= 10 else None
            }
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        # Store analysis in memory for future reference with error handling
        try:
            memory_service = get_intelligent_memory_service(user_id)
            memory_id = memory_service.add_memory(
                text=f"Image Analysis: {analysis['description']}",
                metadata={
                    "type": "image_analysis",
                    "filename": file.filename,
                    "prompt": prompt,
                    "image_size": len(image_data),
                    "insights": analysis.get('insights', []),
                    "suggestions": analysis.get('suggestions', [])
                }
            )
        except Exception as memory_error:
            logger.warning(f"Memory storage failed: {memory_error}")
            memory_id = None
        
        return {
            "success": True,
            "analysis": analysis,
            "memory_id": memory_id,
            "message": "Image analyzed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Image analysis failed")

@router.get("/insights/daily")
async def get_daily_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get daily insights and personalized suggestions based on user activity patterns.
    
    This provides proactive intelligence about user behavior, interests,
    and personalized recommendations for improvement.
    """
    try:
        try:
            proactive_service = get_proactive_service(user_id, db)
            insights = proactive_service.generate_daily_insights()
        except Exception as service_error:
            logger.error(f"Proactive service error: {service_error}")
            return {
                "success": False,
                "error": "Proactive insights service temporarily unavailable",
                "message": "Daily insights service is currently not available. Please try again later.",
                "debug_info": str(service_error) if logger.getEffectiveLevel() <= 10 else None
            }
        
        return {
            "success": True,
            "insights": insights,
            "message": "Daily insights generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate daily insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.get("/insights/patterns")
async def get_user_patterns(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis of user patterns and behavior over time.
    
    This endpoint provides deeper insights into communication patterns,
    topic preferences, and engagement trends.
    """
    try:
        proactive_service = get_proactive_service(user_id, db)
        
        # Get extended pattern analysis
        recent_interactions = proactive_service._get_recent_interactions(days=days)
        
        patterns = {
            "activity_patterns": proactive_service._analyze_activity_patterns(recent_interactions),
            "topic_trends": proactive_service._analyze_topic_trends(recent_interactions),
            "communication_insights": proactive_service._analyze_communication_style(recent_interactions),
            "engagement_score": proactive_service._calculate_engagement_score(recent_interactions),
            "analysis_period": f"{days} days",
            "total_interactions": len(recent_interactions)
        }
        
        return {
            "success": True,
            "patterns": patterns,
            "message": f"Pattern analysis completed for {days} days"
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze patterns: {e}")
        raise HTTPException(status_code=500, detail="Pattern analysis failed")

@router.post("/memory/consolidate")
async def consolidate_memories(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Consolidate and optimize memory storage for better organization.
    
    This runs memory optimization in the background to improve
    memory efficiency and organization.
    """
    try:
        try:
            consolidation_service = get_memory_consolidation_service(user_id)
            
            # Run optimization in background
            background_tasks.add_task(
                consolidation_service.optimize_memory_storage
            )
        except Exception as service_error:
            logger.error(f"Memory consolidation service error: {service_error}")
            return {
                "success": False,
                "error": "Memory consolidation service temporarily unavailable",
                "message": "Memory consolidation service is currently not available. Please try again later.",
                "debug_info": str(service_error) if logger.getEffectiveLevel() <= 10 else None
            }
        
        return {
            "success": True,
            "message": "Memory consolidation started in background",
            "note": "Check back later for optimization results"
        }
        
    except Exception as e:
        logger.error(f"Failed to start memory consolidation: {e}")
        raise HTTPException(status_code=500, detail="Memory consolidation failed")

@router.get("/memory/clusters")
async def get_memory_clusters(
    max_clusters: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get identified clusters of related memories for better organization.
    
    This shows how the AI organizes and relates different memories
    and conversations thematically.
    """
    try:
        consolidation_service = get_memory_consolidation_service(user_id)
        clusters = consolidation_service.identify_memory_clusters(max_clusters)
        
        return {
            "success": True,
            "clusters": clusters,
            "cluster_count": len(clusters),
            "message": "Memory clusters identified successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory clusters: {e}")
        raise HTTPException(status_code=500, detail="Memory clustering failed")

@router.get("/memory/stats")
async def get_enhanced_memory_stats(
    user_id: str = Depends(get_current_user_id)
):
    """
    Get comprehensive memory system statistics and health information.
    
    This provides detailed insights into memory usage, organization,
    and system performance.
    """
    try:
        memory_service = get_intelligent_memory_service(user_id)
        consolidation_service = get_memory_consolidation_service(user_id)
        
        # Get basic memory stats
        basic_stats = memory_service.get_memory_statistics()
        
        # Get memory clusters for organization analysis
        clusters = await consolidation_service.identify_memory_clusters(5)
        
        enhanced_stats = {
            **basic_stats,
            "memory_organization": {
                "identified_clusters": len(clusters),
                "cluster_themes": [cluster['theme'] for cluster in clusters],
                "average_cluster_size": sum(cluster['memory_count'] for cluster in clusters) / len(clusters) if clusters else 0,
                "organization_quality": "excellent" if len(clusters) >= 3 else "developing"
            },
            "memory_health": {
                "storage_efficiency": "optimal" if basic_stats.get('semantic_memory_count', 0) < 100 else "needs_optimization",
                "redundancy_level": "low" if len(clusters) > 0 else "unknown",
                "consolidation_recommended": basic_stats.get('semantic_memory_count', 0) > 50
            }
        }
        
        return {
            "success": True,
            "stats": enhanced_stats,
            "message": "Enhanced memory statistics retrieved"
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhanced memory stats: {e}")
        raise HTTPException(status_code=500, detail="Memory stats retrieval failed")

@router.post("/conversation/summarize")
async def summarize_conversation(
    messages: List[Dict[str, Any]],
    user_id: str = Depends(get_current_user_id)
):
    """
    Summarize a conversation and store it as a consolidated memory.
    
    This helps convert long conversations into meaningful summaries
    for better long-term memory organization.
    """
    try:
        if not messages or len(messages) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 messages to summarize")
        
        consolidation_service = get_memory_consolidation_service(user_id)
        memory_id = await consolidation_service.consolidate_conversation(messages)
        
        if memory_id:
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Conversation summarized and stored successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to summarize conversation")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to summarize conversation: {e}")
        raise HTTPException(status_code=500, detail="Conversation summarization failed")

@router.get("/intelligence/status")
async def get_intelligence_status(
    user_id: str = Depends(get_current_user_id)
):
    """
    Get comprehensive status of all intelligence capabilities.
    
    This shows which AI features are available and their current status.
    """
    try:
        # Check all services
        vision_service = get_vision_service()
        memory_service = get_intelligent_memory_service(user_id)
        
        status = {
            "user_id": user_id,
            "capabilities": {
                "vision_analysis": vision_service.vision_available,
                "semantic_memory": memory_service.chroma_available,
                "short_term_memory": memory_service.redis_client is not None,
                "proactive_insights": True,  # Always available if DB is accessible
                "memory_consolidation": vision_service.vision_available,  # Requires Claude API
                "pattern_recognition": True,
                "learning_system": True
            },
            "memory_status": memory_service.get_memory_statistics(),
            "intelligence_level": "enhanced" if all([
                vision_service.vision_available,
                memory_service.chroma_available,
                memory_service.redis_client is not None
            ]) else "partial",
            "recommendations": []
        }
        
        # Add recommendations based on status
        if not vision_service.vision_available:
            status["recommendations"].append("Configure Claude API key for vision analysis")
        
        if not memory_service.chroma_available:
            status["recommendations"].append("Install ChromaDB for semantic memory")
        
        if not memory_service.redis_client:
            status["recommendations"].append("Configure Redis for session memory")
        
        return {
            "success": True,
            "status": status,
            "message": "Intelligence status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get intelligence status: {e}")
        raise HTTPException(status_code=500, detail="Status retrieval failed")

# Add these routes to the main router
def get_enhanced_router():
    """Get the enhanced capabilities router"""
    try:
        # Test that the router and its dependencies are working
        logger.info(f"🔧 Creating enhanced router with {len(router.routes)} routes")
        
        # Test a simple route to ensure the router is functional
        if not hasattr(router, 'routes') or len(router.routes) == 0:
            logger.error("❌ Enhanced router has no routes!")
            
        # Return the router
        return router
        
    except Exception as e:
        logger.error(f"❌ Error creating enhanced router: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        
        # Return a fallback router with basic functionality
        fallback_router = APIRouter()
        
        @fallback_router.get("/test")
        async def fallback_test():
            return {
                "success": False,
                "message": "Enhanced features temporarily unavailable",
                "error": "Service initialization failed"
            }
            
        return fallback_router 