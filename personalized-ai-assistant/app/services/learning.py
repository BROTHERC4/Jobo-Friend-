from sqlalchemy.orm import Session
from app.models.database import UserProfile, LearnedPattern
from datetime import datetime
from typing import Dict, List, Any

class LearningService:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
    
    def extract_topic(self, text: str) -> str:
        """Extract topic from text"""
        topics = {
            'technology': ['code', 'programming', 'software', 'computer', 'AI', 'tech', 'api', 'database'],
            'personal': ['feel', 'emotion', 'life', 'family', 'friend', 'love', 'happy', 'sad'],
            'work': ['job', 'career', 'project', 'deadline', 'meeting', 'boss', 'colleague'],
            'learning': ['learn', 'study', 'course', 'tutorial', 'understand', 'teach', 'education'],
            'entertainment': ['movie', 'music', 'game', 'book', 'show', 'netflix', 'spotify'],
            'health': ['health', 'exercise', 'diet', 'sleep', 'doctor', 'medicine', 'fitness'],
            'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'destination', 'explore']
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return 'general'
    
    def learn_from_input(self, user_input: str):
        """Extract and store patterns from user input"""
        patterns = []
        
        # Time-based patterns
        current_hour = datetime.utcnow().hour
        if 5 <= current_hour < 12:
            patterns.append(('time_preference', 'morning'))
        elif 12 <= current_hour < 17:
            patterns.append(('time_preference', 'afternoon'))
        elif 17 <= current_hour < 22:
            patterns.append(('time_preference', 'evening'))
        else:
            patterns.append(('time_preference', 'night'))
        
        # Communication style patterns
        if len(user_input) > 200:
            patterns.append(('communication_style', 'verbose'))
        elif len(user_input) < 50:
            patterns.append(('communication_style', 'concise'))
        
        if user_input.strip().endswith('?'):
            patterns.append(('communication_style', 'inquisitive'))
        
        # Topic patterns
        topic = self.extract_topic(user_input)
        if topic != 'general':
            patterns.append(('interest', topic))
        
        # Store patterns
        for pattern_type, pattern_data in patterns:
            self._update_pattern(pattern_type, pattern_data)
    
    def _update_pattern(self, pattern_type: str, pattern_data: str):
        """Update or create pattern"""
        pattern = self.db.query(LearnedPattern).filter(
            LearnedPattern.user_id == self.user_id,
            LearnedPattern.pattern_type == pattern_type,
            LearnedPattern.pattern_data == pattern_data
        ).first()
        
        if pattern:
            pattern.confidence = min(pattern.confidence + 0.1, 1.0)
            pattern.last_used = datetime.utcnow()
        else:
            pattern = LearnedPattern(
                user_id=self.user_id,
                pattern_type=pattern_type,
                pattern_data=pattern_data,
                confidence=0.1
            )
            self.db.add(pattern)
        
        self.db.commit()
    
    def update_profile_from_interaction(self, user_input: str, response: str):
        """Update user profile based on interaction"""
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user_id).first()
        
        # Extract and add new interests
        topic = self.extract_topic(user_input)
        if topic != 'general' and topic not in profile.interests:
            profile.interests = profile.interests + [topic]
        
        # Update communication style based on patterns
        patterns = self.db.query(LearnedPattern).filter(
            LearnedPattern.user_id == self.user_id,
            LearnedPattern.pattern_type == 'communication_style',
            LearnedPattern.confidence > 0.5
        ).all()
        
        if patterns:
            # Update based on most confident pattern
            best_pattern = max(patterns, key=lambda p: p.confidence)
            profile.communication_style['preference'] = best_pattern.pattern_data
        
        profile.updated_at = datetime.utcnow()
        self.db.commit() 