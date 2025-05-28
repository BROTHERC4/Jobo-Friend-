#!/bin/bash

# Start script for Jobo AI Assistant on Railway

echo "Starting Jobo AI Assistant..."
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "Python path: $PYTHONPATH"
echo "Port: ${PORT:-8000}"

echo "Environment variables check:"
echo "DATABASE_URL: ${DATABASE_URL:-NOT_SET}"
echo "REDIS_URL: ${REDIS_URL:-NOT_SET}"
echo "REDIS_PRIVATE_URL: ${REDIS_PRIVATE_URL:-NOT_SET}"
echo "REDIS_PUBLIC_URL: ${REDIS_PUBLIC_URL:-NOT_SET}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "SECRET_KEY: ${SECRET_KEY:+SET}"

echo "Railway services check:"
if [ -n "$DATABASE_URL" ]; then
    echo "✅ Database service detected: $(echo $DATABASE_URL | cut -d'@' -f2)"
else
    echo "❌ Database service not found - using SQLite fallback"
fi

# Check multiple Redis URL formats that Railway might use
if [ -n "$REDIS_URL" ] || [ -n "$REDIS_PRIVATE_URL" ] || [ -n "$REDIS_PUBLIC_URL" ]; then
    echo "✅ Redis service detected"
    # Set REDIS_URL to the first available URL
    export REDIS_URL="${REDIS_URL:-${REDIS_PRIVATE_URL:-$REDIS_PUBLIC_URL}}"
    echo "Using Redis URL: $(echo $REDIS_URL | cut -d'@' -f2)"
else
    echo "❌ Redis service not found - using in-memory fallback"
fi

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info 