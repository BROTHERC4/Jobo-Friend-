from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, FeedbackRequest, UserInsights
from app.services.assistant import PersonalizedAssistant
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "Jobo AI Assistant API is working!",
        "timestamp": "2025-05-28",
        "service": "jobo-ai-assistant",
        "version": "1.0.0"
    }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint with enhanced error handling"""
    try:
        # Validate input
        if not request.user_id or not request.message:
            raise HTTPException(status_code=400, detail="user_id and message are required")
        
        if len(request.message) > 5000:
            raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")
        
        # Initialize assistant
        assistant = PersonalizedAssistant(request.user_id, db)
        
        # Process chat
        result = await assistant.chat(request.message)
        
        # Check for errors in result
        if "error" in result:
            logger.error(f"Assistant error for user {request.user_id}: {result['error']}")
            # Still return a response, but log the error
            
        return ChatResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error for user {request.user_id}: {str(e)}")
        # Return a friendly fallback response
        return ChatResponse(
            response=f"Hello! I'm Jobo, your AI assistant. I received your message: '{request.message[:100]}...' I'm currently experiencing some technical difficulties, but I'm working on getting back to full capacity. Thanks for your patience!",
            interaction_id="emergency_fallback",
            context_used="Emergency fallback mode"
        )

@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Feedback endpoint with improved error handling"""
    try:
        # Validate input
        if not request.user_id or not request.interaction_id:
            raise HTTPException(status_code=400, detail="user_id and interaction_id are required")
        
        if not 0 <= request.satisfaction <= 1:
            raise HTTPException(status_code=400, detail="satisfaction must be between 0 and 1")
        
        from app.models.database import Interaction
        
        interaction = db.query(Interaction).filter(
            Interaction.embedding_id == request.interaction_id,
            Interaction.user_id == request.user_id
        ).first()
        
        if not interaction:
            logger.warning(f"Interaction not found: {request.interaction_id} for user {request.user_id}")
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        interaction.user_satisfaction = request.satisfaction
        db.commit()
        
        logger.info(f"Feedback recorded: {request.satisfaction} for interaction {request.interaction_id}")
        
        return {
            "status": "success", 
            "message": "Thank you for your feedback! This helps me learn and improve.",
            "satisfaction": request.satisfaction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback endpoint error: {str(e)}")
        return {
            "status": "error", 
            "message": "Could not record feedback at this time, but I appreciate your input!"
        }

@router.get("/insights/{user_id}", response_model=UserInsights)
async def get_insights(user_id: str, db: Session = Depends(get_db)):
    """Get user insights with comprehensive error handling"""
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        from app.models.database import LearnedPattern, Interaction, UserProfile
        from sqlalchemy import func
        
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            logger.info(f"Creating insights for new user: {user_id}")
            # Create basic profile if it doesn't exist
            profile = UserProfile(
                user_id=user_id,
                name="User",
                preferences={},
                interests=[],
                communication_style={"formality": "balanced"}
            )
            db.add(profile)
            db.commit()
        
        # Get top patterns
        patterns = db.query(LearnedPattern).filter(
            LearnedPattern.user_id == user_id,
            LearnedPattern.confidence > 0.3
        ).order_by(LearnedPattern.confidence.desc()).limit(10).all()
        
        # Get interaction stats
        stats = db.query(
            func.count(Interaction.id),
            func.avg(Interaction.user_satisfaction)
        ).filter(Interaction.user_id == user_id).first()
        
        # Get topic distribution from recent interactions
        recent_interactions = db.query(Interaction).filter(
            Interaction.user_id == user_id
        ).order_by(Interaction.timestamp.desc()).limit(100).all()
        
        topic_distribution = {}
        for interaction in recent_interactions:
            if interaction.interaction_metadata:
                topic = interaction.interaction_metadata.get('topic', 'general')
                topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
        
        # Ensure at least one topic exists
        if not topic_distribution:
            topic_distribution = {"general": 1}
        
        insights = UserInsights(
            top_patterns=[{
                "type": p.pattern_type,
                "data": p.pattern_data,
                "confidence": round(p.confidence, 2)
            } for p in patterns],
            total_interactions=stats[0] or 0,
            average_satisfaction=round(stats[1], 2) if stats[1] else None,
            topic_distribution=topic_distribution,
            interests=profile.interests or [],
            communication_style=profile.communication_style or {"formality": "balanced"}
        )
        
        logger.info(f"Generated insights for user {user_id}: {insights.total_interactions} interactions")
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insights endpoint error for user {user_id}: {str(e)}")
        # Return basic insights instead of failing
        return UserInsights(
            top_patterns=[],
            total_interactions=0,
            average_satisfaction=None,
            topic_distribution={"general": 1},
            interests=[],
            communication_style={"formality": "balanced"}
        ) 