# Railway Deployment Guide for Jobo AI Assistant

## Quick Fix for Current Issue

The deployment is failing because Railway is looking at the parent directory instead of the `personalized-ai-assistant/` folder. Here are the solutions:

### Option 1: Deploy from Correct Directory (Recommended)

1. **Navigate to the correct directory in Railway**:
   - In Railway dashboard, go to your project settings
   - Under "Source", make sure the root directory is set to `personalized-ai-assistant/`
   - Or redeploy by connecting specifically to the `personalized-ai-assistant` folder

2. **Alternative: Use Railway CLI from correct directory**:
```bash
cd "Jobo (Friend)/personalized-ai-assistant"
railway login
railway init
railway add postgresql
railway add redis
railway up
```

### Option 2: Move Files to Root (If needed)

If Railway can't detect the subdirectory, move all files from `personalized-ai-assistant/` to the root of your repository.

## Environment Variables Required

Make sure these are set in Railway:

```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://... (automatically provided by Railway)
REDIS_URL=redis://... (automatically provided by Railway)
ENVIRONMENT=production
```

## Deployment Steps

1. **Connect Repository**:
   - Connect your GitHub repository to Railway
   - Make sure it's pointing to the `personalized-ai-assistant` directory

2. **Add Services**:
```bash
railway add postgresql
railway add redis
```

3. **Set Environment Variables**:
```bash
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set SECRET_KEY=$(openssl rand -hex 32)
```

4. **Deploy**:
```bash
railway up
```

## Troubleshooting

### Build Fails with "Nixpacks build failed"
- Ensure you're in the `personalized-ai-assistant/` directory
- Check that `requirements.txt`, `Dockerfile`, and `nixpacks.toml` are present
- Verify Python version compatibility

### Database Connection Issues
- Ensure PostgreSQL service is added and running
- Check that `DATABASE_URL` environment variable is set
- Verify database tables are created (they auto-create on first run)

### Redis Connection Issues
- Ensure Redis service is added and running
- Check that `REDIS_URL` environment variable is set

### API Key Issues
- Verify `ANTHROPIC_API_KEY` is set correctly
- Test the key works with a simple API call

## Testing Deployment

Once deployed, test these endpoints:

1. **Health Check**: `GET /health`
2. **API Info**: `GET /api`
3. **Web Interface**: `GET /`
4. **Chat API**: `POST /api/v1/chat`

## Local Testing Before Deployment

```bash
cd "Jobo (Friend)/personalized-ai-assistant"
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your keys
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to test the interface.

## Support

If deployment continues to fail:
1. Check Railway logs for specific error messages
2. Ensure all files are in the correct directory structure
3. Verify all environment variables are set
4. Test locally first to ensure the application works 