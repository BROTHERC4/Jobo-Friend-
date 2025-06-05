from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import UserProfile, Interaction, LearnedPattern
from app.services.memory import IntelligentMemoryService
import logging
import json

logger = logging.getLogger(__name__)

class ProactiveIntelligenceService:
    """
    Proactive intelligence service that provides insights and suggestions
    based on user patterns and behavior analysis.
    
    This service makes Jobo truly intelligent by proactively offering
    help, insights, and suggestions rather than just responding to queries.
    """
    
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        self.memory_service = IntelligentMemoryService(user_id)
    
    async def generate_daily_insights(self) -> Dict[str, Any]:
        """Generate daily insights based on user activity and patterns"""
        try:
            # Get recent interactions
            recent_interactions = self._get_recent_interactions(days=7)
            
            # Analyze patterns
            activity_patterns = self._analyze_activity_patterns(recent_interactions)
            topic_trends = self._analyze_topic_trends(recent_interactions)
            communication_insights = self._analyze_communication_style(recent_interactions)
            
            # Generate suggestions
            suggestions = self._generate_personalized_suggestions(
                activity_patterns, topic_trends, communication_insights
            )
            
            return {
                "date": datetime.utcnow().date().isoformat(),
                "activity_summary": activity_patterns,
                "topic_trends": topic_trends,
                "communication_insights": communication_insights,
                "suggestions": suggestions,
                "engagement_score": self._calculate_engagement_score(recent_interactions)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate daily insights: {e}")
            return {"error": "Could not generate insights"}
    
    def _get_recent_interactions(self, days: int = 7) -> List[Interaction]:
        """Get recent interactions for analysis"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Interaction).filter(
            Interaction.user_id == self.user_id,
            Interaction.timestamp >= cutoff_date
        ).order_by(Interaction.timestamp.desc()).all()
    
    def _analyze_activity_patterns(self, interactions: List[Interaction]) -> Dict[str, Any]:
        """Analyze when and how often the user interacts"""
        if not interactions:
            return {"pattern": "insufficient_data"}
        
        # Group by hour of day
        hourly_activity = {}
        daily_counts = {}
        
        for interaction in interactions:
            hour = interaction.timestamp.hour
            date = interaction.timestamp.date()
            
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        # Find peak activity hours
        peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate consistency
        avg_daily_interactions = sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
        
        return {
            "total_interactions": len(interactions),
            "avg_daily_interactions": round(avg_daily_interactions, 1),
            "peak_hours": [f"{hour}:00" for hour, _ in peak_hours],
            "most_active_hour": f"{peak_hours[0][0]}:00" if peak_hours else None,
            "consistency_score": self._calculate_consistency_score(daily_counts)
        }
    
    def _analyze_topic_trends(self, interactions: List[Interaction]) -> Dict[str, Any]:
        """Analyze trending topics and interests"""
        if not interactions:
            return {"trends": []}
        
        # Extract topics from interactions
        all_text = " ".join([
            (interaction.user_input or "") + " " + (interaction.assistant_response or "")
            for interaction in interactions
        ])
        
        # Simple keyword extraction (could be enhanced with NLP)
        topic_keywords = self._extract_topic_keywords(all_text)
        
        # Analyze recent vs. older interactions for trends
        mid_point = len(interactions) // 2
        recent_text = " ".join([
            (interaction.user_input or "") + " " + (interaction.assistant_response or "")
            for interaction in interactions[:mid_point]
        ])
        older_text = " ".join([
            (interaction.user_input or "") + " " + (interaction.assistant_response or "")
            for interaction in interactions[mid_point:]
        ])
        
        recent_topics = self._extract_topic_keywords(recent_text)
        older_topics = self._extract_topic_keywords(older_text)
        
        # Find emerging topics
        emerging_topics = [
            topic for topic in recent_topics 
            if recent_topics[topic] > older_topics.get(topic, 0)
        ]
        
        return {
            "top_topics": list(topic_keywords.keys())[:5],
            "emerging_topics": emerging_topics[:3],
            "topic_diversity": len(topic_keywords),
            "focus_areas": self._identify_focus_areas(topic_keywords)
        }
    
    def _extract_topic_keywords(self, text: str) -> Dict[str, int]:
        """Extract and count topic-relevant keywords"""
        import re
        
        # Simple keyword extraction - could be enhanced
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter for meaningful words (exclude common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'what', 'when', 'where', 'why', 'this', 'that', 'i', 'you', 'we', 'they', 'it', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might'}
        
        meaningful_words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Count occurrences
        word_counts = {}
        for word in meaningful_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top words
        return dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def _identify_focus_areas(self, topic_keywords: Dict[str, int]) -> List[str]:
        """Identify main focus areas from topics"""
        focus_areas = []
        
        # Technology focus
        tech_words = ['code', 'programming', 'software', 'ai', 'data', 'algorithm', 'tech']
        if any(word in topic_keywords for word in tech_words):
            focus_areas.append("Technology & Programming")
        
        # Learning focus
        learning_words = ['learn', 'study', 'understand', 'knowledge', 'education']
        if any(word in topic_keywords for word in learning_words):
            focus_areas.append("Learning & Education")
        
        # Work focus
        work_words = ['work', 'job', 'project', 'business', 'career']
        if any(word in topic_keywords for word in work_words):
            focus_areas.append("Work & Career")
        
        # Creative focus
        creative_words = ['creative', 'design', 'art', 'music', 'write']
        if any(word in topic_keywords for word in creative_words):
            focus_areas.append("Creative & Design")
        
        return focus_areas
    
    def _analyze_communication_style(self, interactions: List[Interaction]) -> Dict[str, Any]:
        """Analyze user's communication patterns"""
        if not interactions:
            return {"style": "unknown"}
        
        user_inputs = [interaction.user_input for interaction in interactions if interaction.user_input]
        
        if not user_inputs:
            return {"style": "unknown"}
        
        # Analyze message characteristics
        avg_length = sum(len(msg) for msg in user_inputs) / len(user_inputs)
        question_ratio = sum(1 for msg in user_inputs if '?' in msg) / len(user_inputs)
        
        # Determine style
        if avg_length < 50:
            verbosity = "concise"
        elif avg_length < 150:
            verbosity = "moderate"
        else:
            verbosity = "detailed"
        
        if question_ratio > 0.6:
            inquiry_style = "highly_inquisitive"
        elif question_ratio > 0.3:
            inquiry_style = "moderately_inquisitive"
        else:
            inquiry_style = "statement_focused"
        
        return {
            "verbosity": verbosity,
            "avg_message_length": round(avg_length),
            "inquiry_style": inquiry_style,
            "question_ratio": round(question_ratio, 2),
            "total_messages": len(user_inputs)
        }
    
    def _generate_personalized_suggestions(self, activity: Dict, topics: Dict, communication: Dict) -> List[Dict[str, Any]]:
        """Generate personalized suggestions based on analysis"""
        suggestions = []
        
        # Activity-based suggestions
        if activity.get("consistency_score", 0) < 0.5:
            suggestions.append({
                "type": "activity",
                "title": "Consider Regular Check-ins",
                "description": "Your interaction patterns suggest irregular usage. Regular conversations can help me learn your preferences better.",
                "priority": "medium"
            })
        
        # Topic-based suggestions
        if topics.get("topic_diversity", 0) < 3:
            suggestions.append({
                "type": "exploration",
                "title": "Explore New Topics",
                "description": "You might enjoy discussing topics beyond your current focus areas. I can help with various subjects!",
                "priority": "low"
            })
        
        # Communication-based suggestions
        if communication.get("verbosity") == "concise":
            suggestions.append({
                "type": "communication",
                "title": "Detailed Insights Available",
                "description": "I can provide more detailed explanations if helpful. Feel free to ask for deeper analysis on topics of interest.",
                "priority": "low"
            })
        
        # Learning-based suggestions
        if any("Learning" in area for area in topics.get("focus_areas", [])):
            suggestions.append({
                "type": "learning",
                "title": "Learning Path Optimization",
                "description": "I notice you're focused on learning. I can help create structured learning plans and track your progress.",
                "priority": "high"
            })
        
        return suggestions
    
    def _calculate_consistency_score(self, daily_counts: Dict) -> float:
        """Calculate how consistent the user's activity is"""
        if not daily_counts:
            return 0.0
        
        values = list(daily_counts.values())
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        
        # Lower variance = higher consistency
        return max(0, 1 - (variance / avg if avg > 0 else 1))
    
    def _calculate_engagement_score(self, interactions: List[Interaction]) -> float:
        """Calculate user engagement score"""
        if not interactions:
            return 0.0
        
        # Factors: recency, frequency, satisfaction, length
        total_score = 0
        total_weight = 0
        
        for interaction in interactions:
            # Recency score (more recent = higher score)
            days_ago = (datetime.utcnow() - interaction.timestamp).days
            recency_score = max(0, 1 - (days_ago / 7))  # Score decreases over 7 days
            
            # Satisfaction score
            satisfaction_score = interaction.user_satisfaction or 0.5
            
            # Length score (longer conversations suggest engagement)
            length_score = min(1.0, len(interaction.user_input or "") / 100)
            
            interaction_score = (recency_score + satisfaction_score + length_score) / 3
            weight = 1 + recency_score  # Recent interactions weighted more
            
            total_score += interaction_score * weight
            total_weight += weight
        
        return round(total_score / total_weight if total_weight > 0 else 0, 2)

# Global instance management
_proactive_services = {}

def get_proactive_service(user_id: str, db: Session) -> ProactiveIntelligenceService:
    """Get or create proactive service for user"""
    if user_id not in _proactive_services:
        _proactive_services[user_id] = ProactiveIntelligenceService(user_id, db)
    return _proactive_services[user_id] 