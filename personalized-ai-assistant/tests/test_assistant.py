import pytest
from unittest.mock import Mock, patch
from app.services.assistant import PersonalizedAssistant
from app.services.learning import LearningService
from app.services.embeddings import EmbeddingService
from app.models.database import UserProfile

class TestPersonalizedAssistant:
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_user_profile(self):
        """Mock user profile"""
        profile = Mock(spec=UserProfile)
        profile.user_id = "test_user"
        profile.name = "Test User"
        profile.interests = ["technology"]
        profile.communication_style = {"formality": "balanced"}
        return profile
    
    def test_learning_service_extract_topic(self):
        """Test topic extraction from text"""
        learning_service = LearningService("test_user", Mock())
        
        # Test technology topic
        tech_text = "I want to learn programming and software development"
        assert learning_service.extract_topic(tech_text) == "technology"
        
        # Test personal topic
        personal_text = "I'm feeling happy about my family"
        assert learning_service.extract_topic(personal_text) == "personal"
        
        # Test general topic
        general_text = "Hello there"
        assert learning_service.extract_topic(general_text) == "general"
    
    def test_embedding_service(self):
        """Test embedding generation"""
        embedding_service = EmbeddingService()
        
        text = "Hello world"
        embedding = embedding_service.generate_embedding(text)
        
        # Check that embedding is a list of floats
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    @patch('app.services.assistant.anthropic.Anthropic')
    @patch('app.services.assistant.MemoryService')
    @patch('app.services.assistant.EmbeddingService')
    @patch('app.services.assistant.LearningService')
    def test_assistant_initialization(self, mock_learning, mock_embedding, mock_memory, mock_anthropic, mock_db):
        """Test assistant initialization"""
        # Mock the profile query
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        assistant = PersonalizedAssistant("test_user", mock_db)
        
        assert assistant.user_id == "test_user"
        assert assistant.db == mock_db
        mock_anthropic.assert_called_once()
        mock_memory.assert_called_once_with("test_user")
        mock_learning.assert_called_once_with("test_user", mock_db)

if __name__ == "__main__":
    pytest.main([__file__]) 