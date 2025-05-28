# ⚙️ Jobo Configuration Guide

## Required Environment Variables

- `ANTHROPIC_API_KEY`: Your Claude API key (required for full AI capabilities)
- `SECRET_KEY`: A secure random string for session and security

## Automatic Railway Variables

- `DATABASE_URL`: Provided by Railway PostgreSQL service
- `REDIS_URL`: Provided by Railway Redis service

## Optional Settings

- `ENVIRONMENT`: Set to `production` (default) or `development`
- `CHROMA_PERSIST_DIRECTORY`: Path for ChromaDB vector storage (default: `./data/chroma`)

## Example `.env` File
```env
# API Keys
ANTHROPIC_API_KEY=your_claude_api_key_here

# Database URLs (Railway provides these automatically in production)
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://default:password@host:port

# App Configuration
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production
```

## Advanced Configuration
- For advanced vector search, install `sentence-transformers` and `chromadb` (see `requirements-full.txt`)
- ChromaDB directory can be customized with `CHROMA_PERSIST_DIRECTORY`

## Troubleshooting Common Issues
- Ensure all required variables are set in Railway dashboard
- If deploying locally, copy `env.example` to `.env` and fill in your keys
- For full AI, `ANTHROPIC_API_KEY` must be valid
- If using fallback modes, the app will still run but with limited features

## Security Considerations
- Never commit your `.env` file or API keys to version control
- Use strong, unique values for `SECRET_KEY`

## Performance Tuning
- For production, use Railway-provided managed services for PostgreSQL and Redis
- For local development, SQLite and in-memory Redis are used as fallbacks 