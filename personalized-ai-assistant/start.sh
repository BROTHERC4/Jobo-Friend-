#!/bin/bash

# Start script for Jobo AI Assistant on Railway

echo "Starting Jobo AI Assistant..."
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "Python path: $PYTHONPATH"
echo "Port: ${PORT:-8000}"

echo "Environment variables:"
echo "DATABASE_URL: ${DATABASE_URL:+SET}"
echo "REDIS_URL: ${REDIS_URL:+SET}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "SECRET_KEY: ${SECRET_KEY:+SET}"

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info 