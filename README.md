# 🤖 Jobo AI Assistant

A personalized AI assistant that learns from user interactions, adapts to communication styles, and provides increasingly personalized responses using Claude Sonnet API.

## ✅ Current Status
- Fully deployed and operational on Railway
- PostgreSQL and Redis services connected
- Web interface and API endpoints active

## ✨ Features
- **Intelligent Conversations** with Claude Sonnet API
- **Personalized Learning** that adapts to your style
- **Three-Tier Memory System** (Redis + PostgreSQL + Vector DB)
- **Beautiful Web Interface** with real-time chat
- **Pattern Recognition** for interests and communication preferences
- **Feedback Learning** from user satisfaction
- **Insights Dashboard** for analytics on user patterns

## 🏗️ Architecture
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

## 🚀 Quick Start

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

## 📋 API Reference

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

## 🧩 Configuration

See [CONFIGURATION.md](./CONFIGURATION.md) for all required and optional environment variables.

## 🧠 Learning System

Jobo learns from:
- **Communication patterns**: Message length, question frequency, formality
- **Time preferences**: When users are most active
- **Topic interests**: Extracted from conversation content
- **Feedback**: User satisfaction ratings
- **Context usage**: What information is most relevant

## 🛠️ Development

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
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 💬 Support

For issues and questions:
- Check the `/docs` endpoint for API documentation
- Review logs in the `logs/` directory
- Check Railway deployment logs for production issues

---

**Jobo AI Assistant** - Your personalized AI companion that grows with you! 🤖✨ 