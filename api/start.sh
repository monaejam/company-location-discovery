#!/bin/bash
# Railway startup script for the API

echo "🚀 Starting Company Location Discovery API..."
echo "PORT: ${PORT:-8000}"
echo "Environment: ${RAILWAY_ENVIRONMENT:-development}"
echo "Python version: $(python --version)"

# Set Python memory optimization
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Create necessary directories
mkdir -p data/cache
mkdir -p temp/output

echo "📁 Created necessary directories"

# Check if required files exist
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo "✅ Required files found"

# Install dependencies if needed (for Railway's Nixpacks)
if [ ! -d "venv" ] && [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the application with Railway-optimized settings
echo "🌟 Starting uvicorn server on port ${PORT:-8000}..."
exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 60 --access-log
