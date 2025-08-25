#!/usr/bin/env python
"""
Simple startup script for Railway deployment
Handles PORT environment variable properly
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting API server on port {port}")
    
    # Run the FastAPI app
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
