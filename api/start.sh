#!/bin/bash
# Railway startup script for the API

echo "🚀 Starting Company Location Discovery API..."
echo "PORT: ${PORT:-8000}"
echo "Environment: ${RAILWAY_ENVIRONMENT:-development}"

# Set Python memory optimization
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Create necessary directories
mkdir -p data/cache
mkdir -p temp/output

echo "📁 Created necessary directories"

# Start the application with memory-optimized settings
echo "🌟 Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 30 --max-requests 100 --max-requests-jitter 10
