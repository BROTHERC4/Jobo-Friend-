# 🚀 Deploy Your Own Jobo Instance

## Prerequisites
- Railway account
- Anthropic API key
- GitHub account

## 5-Step Deployment
1. Fork this repository
2. Connect to Railway
3. Add PostgreSQL + Redis services
4. Set environment variables
5. Deploy and test

## Detailed Steps

1. **Clone and setup**:
```bash
cd "Jobo (Friend)/personalized-ai-assistant"
```

2. **Install Railway CLI**:
```bash
npm install -g @railway/cli
```

3. **Initialize Railway project**:
```bash
railway login
railway init
```

4. **Add services**:
```bash
railway add postgresql
railway add redis
```

5. **Set environment variables**:
```bash
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set SECRET_KEY=$(openssl rand -hex 32)
```

6. **Deploy**:
```bash
railway up
```

## Verification
- Visit your Railway app URL
- Test the web interface and chat
- Check `/docs` for API documentation
- Use `/health` endpoint for health check

## Local Testing (Optional)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your keys
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to test the interface.

## Support
- For issues, check Railway logs and `/docs` endpoint
- For configuration, see CONFIGURATION.md 