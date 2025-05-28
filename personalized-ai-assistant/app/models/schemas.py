from pydantic import BaseModel, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

# Authentication Schemas
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    display_name: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if len(v) < 2:
            raise ValueError('Username must be at least 2 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, underscores, and dots')
        return v.lower().strip()  # Normalize username

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 4:
            raise ValueError('Password must be at least 4 characters long')
        return v

    @validator('email')
    def email_validation(cls, v):
        if v and v.strip():
            # Basic email validation
            if '@' not in v or '.' not in v.split('@')[-1]:
                raise ValueError('Please enter a valid email address')
            return v.lower().strip()
        return None

class UserLogin(BaseModel):
    username: str
    password: str

    @validator('username')
    def normalize_username(cls, v):
        return v.lower().strip()

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    user_id: str
    is_active: bool
    created_at: datetime

class AuthResponse(BaseModel):
    access_token: str
    user: UserResponse
    expires_in: int
    token_type: str = "bearer"

# Updated Chat Schemas for Authentication
class AuthenticatedChatRequest(BaseModel):
    message: str  # user_id comes from authentication token

# Existing Schemas (preserved for backward compatibility)
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

class AuthenticatedFeedbackRequest(BaseModel):
    interaction_id: str
    satisfaction: float  # user_id comes from authentication token

class UserInsights(BaseModel):
    top_patterns: List[Dict[str, Any]]
    total_interactions: int
    average_satisfaction: Optional[float]
    topic_distribution: Dict[str, int]
    interests: List[str]
    communication_style: Dict[str, str] 