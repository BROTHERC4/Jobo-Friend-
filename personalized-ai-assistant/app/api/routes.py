from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, FeedbackRequest, UserInsights
from app.services.assistant import PersonalizedAssistant

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "Jobo AI Assistant API is working!",
        "timestamp": "2025-05-28",
        "service": "jobo-ai-assistant"
    }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint"""
    try:
        assistant = PersonalizedAssistant(request.user_id, db)
        result = await assistant.chat(request.message)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return ChatResponse(**result)
    except Exception as e:
        # Return a basic response if there's an error
        return ChatResponse(
            response=f"Hello! I'm Jobo, your AI assistant. I received your message: '{request.message}'. I'm currently in basic mode due to a technical issue, but I'm working!",
            interaction_id="basic_mode",
            context_used="Basic fallback mode"
        )

@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Feedback endpoint"""
    try:
        from app.models.database import Interaction
        
        interaction = db.query(Interaction).filter(
            Interaction.embedding_id == request.interaction_id,
            Interaction.user_id == request.user_id
        ).first()
        
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        interaction.user_satisfaction = request.satisfaction
        db.commit()
        
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        return {"status": "error", "message": f"Could not record feedback: {str(e)}"}

@router.get("/insights/{user_id}", response_model=UserInsights)
async def get_insights(user_id: str, db: Session = Depends(get_db)):
    """Get user insights"""
    try:
        from app.models.database import LearnedPattern, Interaction, UserProfile
        from sqlalchemy import func
        
        # Get top patterns
        patterns = db.query(LearnedPattern).filter(
            LearnedPattern.user_id == user_id,
            LearnedPattern.confidence > 0.5
        ).order_by(LearnedPattern.confidence.desc()).limit(10).all()
        
        # Get interaction stats
        stats = db.query(
            func.count(Interaction.id),
            func.avg(Interaction.user_satisfaction)
        ).filter(Interaction.user_id == user_id).first()
        
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get topic distribution
        recent_interactions = db.query(Interaction).filter(
            Interaction.user_id == user_id
        ).order_by(Interaction.timestamp.desc()).limit(100).all()
        
        topic_distribution = {}
        for interaction in recent_interactions:
            topic = interaction.interaction_metadata.get('topic', 'general')  # Updated to use interaction_metadata
            topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
        
        return UserInsights(
            top_patterns=[{
                "type": p.pattern_type,
                "data": p.pattern_data,
                "confidence": p.confidence
            } for p in patterns],
            total_interactions=stats[0] or 0,
            average_satisfaction=stats[1],
            topic_distribution=topic_distribution,
            interests=profile.interests,
            communication_style=profile.communication_style
        )
    except Exception as e:
        # Return basic insights if there's an error
        return UserInsights(
            top_patterns=[],
            total_interactions=0,
            average_satisfaction=None,
            topic_distribution={"general": 1},
            interests=[],
            communication_style={"formality": "balanced"}
        ) 