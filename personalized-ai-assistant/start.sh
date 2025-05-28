#!/bin/bash

# Start script for Jobo AI Assistant on Railway

echo "Starting Jobo AI Assistant..."
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "Python path: $PYTHONPATH"
echo "Port: ${PORT:-8000}"

echo "Environment variables:"
echo "DATABASE_URL: ${DATABASE_URL:+SET (${DATABASE_URL:0:20}...)}"
echo "REDIS_URL: ${REDIS_URL:+SET (${REDIS_URL:0:20}...)}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "SECRET_KEY: ${SECRET_KEY:+SET}"

echo "Railway services check:"
if [ -n "$DATABASE_URL" ]; then
    echo "✅ Database service detected"
else
    echo "❌ Database service not found - using SQLite fallback"
fi

if [ -n "$REDIS_URL" ]; then
    echo "✅ Redis service detected"
else
    echo "❌ Redis service not found - using in-memory fallback"
fi

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info 