#!/bin/bash
# Railway startup script for the API

echo "🚀 Starting Company Location Discovery API..."
echo "PORT: ${PORT:-8000}"
echo "Environment: ${RAILWAY_ENVIRONMENT:-development}"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 30
