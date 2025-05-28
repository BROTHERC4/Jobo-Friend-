# Railway Deployment Fix Guide

## Issues Found in Logs:
1. ❌ Database service not found - using SQLite fallback
2. ❌ Redis service not found - using in-memory fallback  
3. ❌ Claude API error: "unexpected keyword argument 'proxies'"
4. ❌ SentenceTransformers import error

## Fixes Applied:

### 1. Updated Requirements
- Simplified `requirements.txt` to remove heavy dependencies
- Made ML libraries optional with fallback methods
- Fixed Anthropic API version compatibility

### 2. Services Configuration
You need to add PostgreSQL and Redis services to your Railway project:

```bash
# Add PostgreSQL service
railway add postgresql

# Add Redis service  
railway add redis

# Deploy the updated code
railway up
```

### 3. Environment Variables
Make sure these are set in Railway dashboard:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `SECRET_KEY`: A secure random string

### 4. Railway Service URLs
After adding services, Railway will automatically provide:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL` or `REDIS_PRIVATE_URL`: Redis connection string

## Verification Steps:

1. Check Railway dashboard that services are added
2. Verify environment variables are set
3. Deploy and check logs for service detection
4. Test the chat functionality

## Expected Log Output After Fix:
```
✅ Database service detected: postgresql://...
✅ Redis service detected  
Claude API initialized successfully
```

## If Services Still Not Detected:

Check Railway dashboard and ensure:
1. PostgreSQL service is running
2. Redis service is running
3. Environment variables are properly set
4. Services are linked to your app

## Manual Environment Variable Check:
You can manually set these in Railway if auto-detection fails:
- `DATABASE_URL=postgresql://username:password@host:port/database`
- `REDIS_URL=redis://host:port` 