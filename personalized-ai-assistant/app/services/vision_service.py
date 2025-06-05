import base64
import anthropic
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class VisionService:
    """
    Vision service for image analysis using Claude 3.5 Sonnet's vision capabilities.
    
    This service enables Jobo to understand and analyze images, screenshots,
    documents, charts, and other visual content.
    """
    
    def __init__(self):
        self.client = None
        self.vision_available = False
        self._initialize_vision_client()
    
    def _initialize_vision_client(self):
        """Initialize Claude vision client"""
        try:
            if settings.anthropic_api_key:
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self.vision_available = True
                logger.info("✅ Vision service initialized successfully")
            else:
                logger.warning("❌ Vision service unavailable - no API key")
        except Exception as e:
            logger.error(f"❌ Failed to initialize vision service: {e}")
    
    async def analyze_image(self, image_data: bytes, prompt: str = "Analyze this image") -> Dict[str, Any]:
        """
        Analyze an image using Claude's vision capabilities.
        
        Args:
            image_data: Raw image bytes
            prompt: Analysis prompt
            
        Returns:
            Analysis results with description, insights, and metadata
        """
        if not self.vision_available:
            return {
                "error": "Vision service not available",
                "description": "Image analysis requires Claude API access"
            }
        
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image type (simplified)
            image_type = "image/jpeg"  # Default, could be enhanced
            
            # Analyze image with Claude
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": f"{prompt}\n\nPlease provide a detailed analysis including:\n1. What you see in the image\n2. Key insights or observations\n3. Any relevant context or suggestions"
                        }
                    ]
                }]
            )
            
            analysis = response.content[0].text
            
            return {
                "success": True,
                "description": analysis,
                "insights": self._extract_insights(analysis),
                "suggestions": self._extract_suggestions(analysis),
                "metadata": {
                    "image_size": len(image_data),
                    "analysis_length": len(analysis),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {e}")
            return {
                "error": str(e),
                "description": "Failed to analyze image"
            }
    
    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis text"""
        # Simple extraction - could be enhanced with NLP
        insights = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['insight', 'notable', 'important', 'key']):
                insights.append(line.strip())
        
        return insights[:5]  # Limit to top 5
    
    def _extract_suggestions(self, analysis: str) -> List[str]:
        """Extract suggestions from analysis text"""
        suggestions = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'consider', 'could', 'might']):
                suggestions.append(line.strip())
        
        return suggestions[:3]  # Limit to top 3

# Global instance
_vision_service = None

def get_vision_service() -> VisionService:
    """Get the global vision service instance"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service 