# Jobo AI Assistant

A personalized AI assistant that learns from user interactions, adapts to communication styles, and provides increasingly personalized responses using Claude Sonnet API.

## Features

- **Personalized Learning**: Learns from every interaction to adapt responses
- **Three-Tier Memory System**: 
  - Redis for short-term conversation memory
  - PostgreSQL for structured user data
  - ChromaDB for semantic vector search
- **Communication Style Adaptation**: Adjusts formality and verbosity based on user patterns
- **Interest Tracking**: Identifies and remembers user interests and topics
- **Feedback System**: Learns from user satisfaction ratings
- **Insights Dashboard**: Provides analytics on user patterns and preferences

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (Railway-hosted)
- **Vector DB**: ChromaDB (embedded mode)
- **Cache**: Redis (Railway-hosted)
- **AI**: Claude Sonnet API (Anthropic)
- **Deployment**: Railway

## Quick Start

### Local Development

1. **Clone and setup**:
```bash
cd "Jobo (Friend)/personalized-ai-assistant"
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment setup**:
```bash
cp env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_claude_api_key_here
# DATABASE_URL=postgresql://user:password@localhost/jobo
# REDIS_URL=redis://localhost:6379
# SECRET_KEY=your_secret_key_here
```

3. **Run locally**:
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

### Railway Deployment

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
```

2. **Deploy**:
```bash
railway login
railway init
railway add postgresql
railway add redis
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway up
```

## API Endpoints

### Chat
```bash
POST /api/v1/chat
{
  "user_id": "user123",
  "message": "Hello Jobo!"
}
```

### Feedback
```bash
POST /api/v1/feedback
{
  "user_id": "user123",
  "interaction_id": "interaction_id",
  "satisfaction": 0.8
}
```

### User Insights
```bash
GET /api/v1/insights/user123
```

## Example Usage

```python
import requests

# Chat with Jobo
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "user_id": "test_user",
    "message": "Hi Jobo, I'm interested in learning Python programming"
})

print(response.json())
# {
#   "response": "Hello! I'd be happy to help you learn Python programming...",
#   "interaction_id": "abc123",
#   "context_used": "User Profile: - Name: User - Interests: Not specified..."
# }
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Claude API    │    │   ChromaDB      │
│                 │────│                 │    │   (Vectors)     │
│   - Routes      │    │   - Responses   │    │                 │
│   - Middleware  │    │   - Context     │    └─────────────────┘
└─────────────────┘    └─────────────────┘              │
         │                                               │
         │              ┌─────────────────┐              │
         └──────────────│   PostgreSQL    │──────────────┘
                        │                 │
                        │   - Profiles    │
                        │   - Interactions│
                        │   - Patterns    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │     Redis       │
                        │                 │
                        │ - Short Memory  │
                        │ - Sessions      │
                        └─────────────────┘
```

## Learning System

Jobo learns from:
- **Communication patterns**: Message length, question frequency, formality
- **Time preferences**: When users are most active
- **Topic interests**: Extracted from conversation content
- **Feedback**: User satisfaction ratings
- **Context usage**: What information is most relevant

## Development

### Project Structure
```
app/
├── __init__.py
├── main.py              # FastAPI app
├── config.py            # Environment configuration
├── models/
│   ├── database.py      # SQLAlchemy models
│   └── schemas.py       # Pydantic schemas
├── services/
│   ├── assistant.py     # Main AI assistant logic
│   ├── memory.py        # Memory management
│   ├── learning.py      # Learning algorithms
│   └── embeddings.py    # Embedding generation
├── api/
│   └── routes.py        # API endpoints
└── utils/
    └── helpers.py       # Utility functions
```

### Testing
```bash
# Run tests
pytest tests/

# Test specific endpoint
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello!"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check the `/docs` endpoint for API documentation
- Review logs in the `logs/` directory
- Check Railway deployment logs for production issues

---

**Jobo AI Assistant** - Your personalized AI companion that grows with you! 🤖✨ 