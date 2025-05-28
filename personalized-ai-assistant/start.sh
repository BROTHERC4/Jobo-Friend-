#!/bin/bash

# Start script for Jobo AI Assistant on Railway

echo "Starting Jobo AI Assistant..."

# Set default port if not provided
export PORT=${PORT:-8000}

# Create necessary directories
mkdir -p data/chroma
mkdir -p logs

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 