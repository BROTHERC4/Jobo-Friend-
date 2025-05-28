from sqlalchemy.orm import Session
from app.models.database import UserProfile, LearnedPattern
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
    
    def extract_topic(self, text: str) -> str:
        """Extract topic from text with improved keyword matching"""
        topics = {
            'technology': [
                'code', 'programming', 'software', 'computer', 'AI', 'tech', 'api', 'database',
                'python', 'javascript', 'react', 'node', 'html', 'css', 'machine learning',
                'development', 'github', 'coding', 'algorithm', 'data science', 'web dev',
                'mobile app', 'frontend', 'backend', 'cloud', 'docker', 'kubernetes'
            ],
            'personal': [
                'feel', 'emotion', 'life', 'family', 'friend', 'love', 'happy', 'sad',
                'relationship', 'feelings', 'mood', 'personal', 'myself', 'thoughts',
                'emotions', 'heart', 'soul', 'mental health', 'wellbeing', 'stress'
            ],
            'work': [
                'job', 'career', 'project', 'deadline', 'meeting', 'boss', 'colleague',
                'office', 'work', 'business', 'professional', 'interview', 'resume',
                'salary', 'promotion', 'team', 'management', 'corporate', 'startup'
            ],
            'learning': [
                'learn', 'study', 'course', 'tutorial', 'understand', 'teach', 'education',
                'school', 'university', 'book', 'reading', 'knowledge', 'skill',
                'training', 'practice', 'lesson', 'academic', 'research', 'homework'
            ],
            'entertainment': [
                'movie', 'music', 'game', 'book', 'show', 'netflix', 'spotify',
                'film', 'series', 'gaming', 'entertainment', 'fun', 'hobby',
                'youtube', 'social media', 'meme', 'comedy', 'drama', 'action'
            ],
            'health': [
                'health', 'exercise', 'diet', 'sleep', 'doctor', 'medicine', 'fitness',
                'workout', 'nutrition', 'wellness', 'medical', 'hospital', 'therapy',
                'mental health', 'physical', 'body', 'mind', 'meditation', 'yoga'
            ],
            'travel': [
                'travel', 'trip', 'vacation', 'flight', 'hotel', 'destination', 'explore',
                'journey', 'adventure', 'tourism', 'country', 'city', 'culture',
                'backpacking', 'sightseeing', 'holiday', 'abroad', 'international'
            ],
            'food': [
                'food', 'cooking', 'recipe', 'restaurant', 'eat', 'meal', 'dinner',
                'lunch', 'breakfast', 'cuisine', 'chef', 'kitchen', 'taste',
                'delicious', 'hungry', 'dining', 'culinary', 'ingredients'
            ],
            'finance': [
                'money', 'finance', 'budget', 'investment', 'savings', 'bank',
                'crypto', 'stocks', 'economy', 'financial', 'income', 'expense',
                'debt', 'credit', 'loan', 'insurance', 'tax', 'wealth'
            ]
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topics.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Give higher weight to exact matches
                    if f' {keyword} ' in f' {text_lower} ':
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return 'general'
    
    def analyze_communication_style(self, user_input: str) -> Dict[str, str]:
        """Analyze communication style from user input"""
        style = {}
        
        # Analyze formality
        formal_indicators = ['please', 'thank you', 'could you', 'would you', 'may i']
        informal_indicators = ['hey', 'hi', 'yeah', 'ok', 'cool', 'awesome']
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in user_input.lower())
        informal_count = sum(1 for indicator in informal_indicators if indicator in user_input.lower())
        
        if formal_count > informal_count:
            style['formality'] = 'formal'
        elif informal_count > formal_count:
            style['formality'] = 'informal'
        else:
            style['formality'] = 'balanced'
        
        # Analyze verbosity
        word_count = len(user_input.split())
        if word_count > 50:
            style['verbosity'] = 'verbose'
        elif word_count < 10:
            style['verbosity'] = 'concise'
        else:
            style['verbosity'] = 'moderate'
        
        # Analyze question tendency
        if user_input.strip().endswith('?') or any(word in user_input.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            style['interaction_type'] = 'inquisitive'
        elif any(word in user_input.lower() for word in ['tell me', 'explain', 'describe']):
            style['interaction_type'] = 'seeking_explanation'
        else:
            style['interaction_type'] = 'conversational'
        
        return style
    
    def learn_from_input(self, user_input: str):
        """Extract and store patterns from user input with enhanced analysis"""
        try:
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
            
            # Communication style analysis
            style = self.analyze_communication_style(user_input)
            for style_type, style_value in style.items():
                patterns.append((f'communication_{style_type}', style_value))
            
            # Topic patterns
            topic = self.extract_topic(user_input)
            if topic != 'general':
                patterns.append(('interest', topic))
            
            # Sentiment patterns (basic)
            positive_words = ['good', 'great', 'awesome', 'excellent', 'love', 'like', 'happy', 'excited']
            negative_words = ['bad', 'terrible', 'hate', 'dislike', 'sad', 'angry', 'frustrated']
            
            user_lower = user_input.lower()
            positive_count = sum(1 for word in positive_words if word in user_lower)
            negative_count = sum(1 for word in negative_words if word in user_lower)
            
            if positive_count > negative_count:
                patterns.append(('sentiment', 'positive'))
            elif negative_count > positive_count:
                patterns.append(('sentiment', 'negative'))
            
            # Message length patterns
            if len(user_input) > 200:
                patterns.append(('message_length', 'long'))
            elif len(user_input) < 20:
                patterns.append(('message_length', 'short'))
            else:
                patterns.append(('message_length', 'medium'))
            
            # Store patterns
            for pattern_type, pattern_data in patterns:
                self._update_pattern(pattern_type, pattern_data)
                
            logger.debug(f"Learned {len(patterns)} patterns from user input for {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to learn from input for user {self.user_id}: {e}")
    
    def _update_pattern(self, pattern_type: str, pattern_data: str):
        """Update or create pattern with improved confidence calculation"""
        try:
            pattern = self.db.query(LearnedPattern).filter(
                LearnedPattern.user_id == self.user_id,
                LearnedPattern.pattern_type == pattern_type,
                LearnedPattern.pattern_data == pattern_data
            ).first()
            
            if pattern:
                # Increase confidence but with diminishing returns
                old_confidence = pattern.confidence
                increment = 0.1 * (1 - old_confidence)  # Diminishing returns
                pattern.confidence = min(old_confidence + increment, 0.95)  # Cap at 0.95
                pattern.last_used = datetime.utcnow()
                logger.debug(f"Updated pattern {pattern_type}:{pattern_data} confidence from {old_confidence:.2f} to {pattern.confidence:.2f}")
            else:
                pattern = LearnedPattern(
                    user_id=self.user_id,
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    confidence=0.1
                )
                self.db.add(pattern)
                logger.debug(f"Created new pattern {pattern_type}:{pattern_data} with confidence 0.1")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update pattern for user {self.user_id}: {e}")
            self.db.rollback()
    
    def update_profile_from_interaction(self, user_input: str, response: str):
        """Update user profile based on interaction with enhanced intelligence"""
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user_id).first()
            
            if not profile:
                logger.warning(f"No profile found for user {self.user_id}")
                return
            
            # Extract and add new interests
            topic = self.extract_topic(user_input)
            if topic != 'general' and topic not in profile.interests:
                profile.interests = profile.interests + [topic]
                logger.info(f"Added new interest '{topic}' for user {self.user_id}")
            
            # Update communication style based on patterns
            communication_patterns = self.db.query(LearnedPattern).filter(
                LearnedPattern.user_id == self.user_id,
                LearnedPattern.pattern_type.like('communication_%'),
                LearnedPattern.confidence > 0.3
            ).all()
            
            if communication_patterns:
                # Group patterns by communication aspect
                style_updates = {}
                for pattern in communication_patterns:
                    aspect = pattern.pattern_type.replace('communication_', '')
                    if aspect not in style_updates or pattern.confidence > style_updates[aspect]['confidence']:
                        style_updates[aspect] = {
                            'value': pattern.pattern_data,
                            'confidence': pattern.confidence
                        }
                
                # Update profile with most confident patterns
                for aspect, data in style_updates.items():
                    if data['confidence'] > 0.5:  # Only update if we're confident
                        profile.communication_style[aspect] = data['value']
                        logger.debug(f"Updated communication style {aspect} to {data['value']} for user {self.user_id}")
            
            # Update preferences based on positive sentiment patterns
            positive_topics = self.db.query(LearnedPattern).filter(
                LearnedPattern.user_id == self.user_id,
                LearnedPattern.pattern_type == 'interest',
                LearnedPattern.confidence > 0.4
            ).all()
            
            if positive_topics:
                preferred_topics = [p.pattern_data for p in positive_topics]
                profile.preferences['favorite_topics'] = preferred_topics
                logger.debug(f"Updated favorite topics for user {self.user_id}: {preferred_topics}")
            
            profile.updated_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update profile for user {self.user_id}: {e}")
            self.db.rollback() 