from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, User
from app.models.schemas import (
    ChatRequest, ChatResponse, FeedbackRequest, UserInsights,
    AuthenticatedChatRequest, AuthenticatedFeedbackRequest
)
from app.services.assistant import PersonalizedAssistant
from app.api.auth import get_current_user
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
        "version": "2.0.0"
    }

# Authenticated Endpoints (New Secure API)
@router.post("/chat", response_model=ChatResponse)
async def authenticated_chat(
    request: AuthenticatedChatRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Main chat endpoint with authentication (secure)"""
    try:
        # Validate input
        if not request.message:
            raise HTTPException(status_code=400, detail="message is required")
        
        if len(request.message) > 5000:
            raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")
        
        # Initialize assistant with authenticated user's user_id
        assistant = PersonalizedAssistant(current_user.user_id, db)
        
        # Process chat
        result = await assistant.chat(request.message)
        
        # Check for errors in result
        if "error" in result:
            logger.error(f"Assistant error for user {current_user.username}: {result['error']}")
            # Still return a response, but log the error
        
        # Personalize response with user's display name
        if "response" in result and current_user.display_name:
            # Add a touch of personalization without changing the AI's core response
            logger.info(f"Chat processed for authenticated user {current_user.username}")
            
        return ChatResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error for user {current_user.username}: {str(e)}")
        # Return a friendly fallback response
        return ChatResponse(
            response=f"Hello {current_user.display_name or current_user.username}! I'm Jobo, your AI assistant. I received your message: '{request.message[:100]}...' I'm currently experiencing some technical difficulties, but I'm working on getting back to full capacity. Thanks for your patience!",
            interaction_id="emergency_fallback",
            context_used="Emergency fallback mode"
        )

@router.post("/feedback")
async def authenticated_feedback(
    request: AuthenticatedFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Feedback endpoint with authentication (secure)"""
    try:
        # Validate input
        if not request.interaction_id:
            raise HTTPException(status_code=400, detail="interaction_id is required")
        
        if not 0 <= request.satisfaction <= 1:
            raise HTTPException(status_code=400, detail="satisfaction must be between 0 and 1")
        
        from app.models.database import Interaction
        
        # Ensure user can only provide feedback on their own interactions
        interaction = db.query(Interaction).filter(
            Interaction.embedding_id == request.interaction_id,
            Interaction.user_id == current_user.user_id
        ).first()
        
        if not interaction:
            logger.warning(f"Interaction not found: {request.interaction_id} for user {current_user.username}")
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        interaction.user_satisfaction = request.satisfaction
        db.commit()
        
        logger.info(f"Feedback recorded: {request.satisfaction} for interaction {request.interaction_id} by user {current_user.username}")
        
        return {
            "status": "success", 
            "message": "Thank you for your feedback! This helps me learn and improve.",
            "satisfaction": request.satisfaction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback endpoint error for user {current_user.username}: {str(e)}")
        return {
            "status": "error", 
            "message": "Could not record feedback at this time, but I appreciate your input!"
        }

@router.get("/insights", response_model=UserInsights)
async def authenticated_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user insights with authentication (secure)"""
    try:
        from app.models.database import LearnedPattern, Interaction, UserProfile
        from sqlalchemy import func
        
        # Get user profile (guaranteed to exist since user is authenticated)
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
        
        if not profile:
            logger.info(f"Creating insights for authenticated user: {current_user.username}")
            # Create basic profile if it doesn't exist
            profile = UserProfile(
                user_id=current_user.user_id,
                name=current_user.display_name or current_user.username,
                preferences={},
                interests=[],
                communication_style={"formality": "balanced"}
            )
            db.add(profile)
            db.commit()
        
        # Get top patterns for this user only
        patterns = db.query(LearnedPattern).filter(
            LearnedPattern.user_id == current_user.user_id,
            LearnedPattern.confidence > 0.3
        ).order_by(LearnedPattern.confidence.desc()).limit(10).all()
        
        # Get interaction stats for this user only
        stats = db.query(
            func.count(Interaction.id),
            func.avg(Interaction.user_satisfaction)
        ).filter(Interaction.user_id == current_user.user_id).first()
        
        # Get topic distribution from recent interactions for this user only
        recent_interactions = db.query(Interaction).filter(
            Interaction.user_id == current_user.user_id
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
        
        logger.info(f"Generated insights for authenticated user {current_user.username}: {insights.total_interactions} interactions")
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insights endpoint error for user {current_user.username}: {str(e)}")
        # Return basic insights instead of failing
        return UserInsights(
            top_patterns=[],
            total_interactions=0,
            average_satisfaction=None,
            topic_distribution={"general": 1},
            interests=[],
            communication_style={"formality": "balanced"}
        )

# Legacy Endpoints (For Backward Compatibility - Deprecated)
@router.post("/legacy/chat", response_model=ChatResponse, deprecated=True)
async def legacy_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Legacy chat endpoint (deprecated - use authenticated /chat instead)"""
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
        logger.error(f"Legacy chat endpoint error for user {request.user_id}: {str(e)}")
        # Return a friendly fallback response
        return ChatResponse(
            response=f"Hello! I'm Jobo, your AI assistant. I received your message: '{request.message[:100]}...' I'm currently experiencing some technical difficulties, but I'm working on getting back to full capacity. Thanks for your patience!",
            interaction_id="emergency_fallback",
            context_used="Emergency fallback mode"
        )

@router.post("/legacy/feedback", deprecated=True)
async def legacy_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Legacy feedback endpoint (deprecated - use authenticated /feedback instead)"""
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
        
        logger.info(f"Legacy feedback recorded: {request.satisfaction} for interaction {request.interaction_id}")
        
        return {
            "status": "success", 
            "message": "Thank you for your feedback! This helps me learn and improve.",
            "satisfaction": request.satisfaction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Legacy feedback endpoint error: {str(e)}")
        return {
            "status": "error", 
            "message": "Could not record feedback at this time, but I appreciate your input!"
        }

@router.get("/legacy/insights/{user_id}", response_model=UserInsights, deprecated=True)
async def legacy_insights(user_id: str, db: Session = Depends(get_db)):
    """Legacy insights endpoint (deprecated - use authenticated /insights instead)"""
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
        
        logger.info(f"Generated legacy insights for user {user_id}: {insights.total_interactions} interactions")
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Legacy insights endpoint error for user {user_id}: {str(e)}")
        # Return basic insights instead of failing
        return UserInsights(
            top_patterns=[],
            total_interactions=0,
            average_satisfaction=None,
            topic_distribution={"general": 1},
            interests=[],
            communication_style={"formality": "balanced"}
        ) 