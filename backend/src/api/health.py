from fastapi import APIRouter, HTTPException, status as http_status
from datetime import datetime
from loguru import logger

health_router = APIRouter()

@health_router.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Global Supply Chain API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now(),
        "endpoints": {
            "stream_chat": "/api/v1/stream-chat/stream",
            "development_stream": "/api/v1/stream-chat/dummy_stream",
            "user_registration": "/api/v1/update-create/register_user",
            "memory_management": "/api/v1/update-create/update_session_data",
            "health": "/health",
            "docs": "/docs"
        }
    }

@health_router.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "Global Supply Chain API",
            "version": "1.0.0",
            "timestamp": datetime.now(),
            "components": {
                "fastapi": "active",
                "streaming": "enabled",
                "api_routes": "active"
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )