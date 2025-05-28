from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    interaction_id: str
    context_used: Optional[str] = None

class FeedbackRequest(BaseModel):
    user_id: str
    interaction_id: str
    satisfaction: float

class UserInsights(BaseModel):
    top_patterns: List[Dict[str, Any]]
    total_interactions: int
    average_satisfaction: Optional[float]
    topic_distribution: Dict[str, int]
    interests: List[str]
    communication_style: Dict[str, str] 