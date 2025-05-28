#!/bin/bash

# Start script for Jobo AI Assistant on Railway

echo "🚀 Starting Jobo AI Assistant..."
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo ""
echo "🐍 Python environment:"
python --version
echo "Python path: $PYTHONPATH"
echo "Port: ${PORT:-8000}"

echo ""
echo "🔧 Environment variables check:"
echo "DATABASE_URL: ${DATABASE_URL:-NOT_SET}"
echo "REDIS_URL: ${REDIS_URL:-NOT_SET}"
echo "REDIS_PRIVATE_URL: ${REDIS_PRIVATE_URL:-NOT_SET}"
echo "REDIS_PUBLIC_URL: ${REDIS_PUBLIC_URL:-NOT_SET}"
echo "REDISCLOUD_URL: ${REDISCLOUD_URL:-NOT_SET}"
echo "REDIS_TLS_URL: ${REDIS_TLS_URL:-NOT_SET}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "SECRET_KEY: ${SECRET_KEY:+SET}"

echo ""
echo "🔍 Railway services check:"
if [ -n "$DATABASE_URL" ]; then
    echo "✅ Database service detected: $(echo $DATABASE_URL | cut -d'@' -f2)"
else
    echo "❌ Database service not found - using SQLite fallback"
    echo "   👉 To fix: Add PostgreSQL service in Railway dashboard"
    echo "   📋 Command: railway add postgresql"
fi

# Check multiple Redis URL formats that Railway might use
REDIS_FOUND=false
if [ -n "$REDIS_URL" ]; then
    echo "✅ Redis service detected via REDIS_URL"
    REDIS_FOUND=true
elif [ -n "$REDIS_PRIVATE_URL" ]; then
    echo "✅ Redis service detected via REDIS_PRIVATE_URL"
    export REDIS_URL="$REDIS_PRIVATE_URL"
    REDIS_FOUND=true
elif [ -n "$REDIS_PUBLIC_URL" ]; then
    echo "✅ Redis service detected via REDIS_PUBLIC_URL"
    export REDIS_URL="$REDIS_PUBLIC_URL"
    REDIS_FOUND=true
elif [ -n "$REDISCLOUD_URL" ]; then
    echo "✅ Redis service detected via REDISCLOUD_URL"
    export REDIS_URL="$REDISCLOUD_URL"
    REDIS_FOUND=true
elif [ -n "$REDIS_TLS_URL" ]; then
    echo "✅ Redis service detected via REDIS_TLS_URL"
    export REDIS_URL="$REDIS_TLS_URL"
    REDIS_FOUND=true
fi

if [ "$REDIS_FOUND" = false ]; then
    echo "❌ Redis service not found - using in-memory fallback"
    echo "   👉 To fix: Add Redis service in Railway dashboard"
    echo "   📋 Command: railway add redis"
fi

echo ""
echo "🧠 AI Service check:"
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ Anthropic API key detected - full AI capabilities enabled"
else
    echo "❌ Anthropic API key not found - using fallback responses"
    echo "   👉 To fix: Set ANTHROPIC_API_KEY in Railway dashboard"
fi

echo ""
echo "📦 Installed packages check:"
echo "Anthropic version: $(python -c "import anthropic; print(anthropic.__version__)" 2>/dev/null || echo "Not installed")"
echo "FastAPI version: $(python -c "import fastapi; print(fastapi.__version__)" 2>/dev/null || echo "Not installed")"

echo ""
echo "🎯 Service Status Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
[ -n "$DATABASE_URL" ] && echo "Database:  ✅ Connected" || echo "Database:  ❌ Fallback Mode"
[ "$REDIS_FOUND" = true ] && echo "Redis:     ✅ Connected" || echo "Redis:     ❌ Fallback Mode"  
[ -n "$ANTHROPIC_API_KEY" ] && echo "AI:        ✅ Full Power" || echo "AI:        ❌ Fallback Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "🌟 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info 