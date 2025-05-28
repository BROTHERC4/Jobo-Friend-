from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, FeedbackRequest, UserInsights
from app.services.assistant import PersonalizedAssistant

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint"""
    assistant = PersonalizedAssistant(request.user_id, db)
    result = await assistant.chat(request.message)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ChatResponse(**result)

@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Feedback endpoint"""
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

@router.get("/insights/{user_id}", response_model=UserInsights)
async def get_insights(user_id: str, db: Session = Depends(get_db)):
    """Get user insights"""
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
        topic = interaction.interaction_metadata.get('topic', 'general')
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