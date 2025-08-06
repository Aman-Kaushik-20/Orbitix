import uvicorn
import time
from datetime import datetime
from contextlib import asynccontextmanager

import src.services.chat_service as chat_service
import src.services.team_agent_service as team_agent_service
import src.services.working_memory_service as working_memory_service
import src.services.episodic_memory_service as episodic_memory_service


from fastapi import FastAPI, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.core.container import Container

from src.api import development_stream, user_registration, chat_streaming, memory_management, health
from src.api.development_stream import development_stream_router
from src.api.user_registration import user_registration_router
from src.api.chat_streaming import chat_streaming_router
from src.api.memory_management import memory_management_router
from src.api.health import health_router


# Configuration
API_PREFIX = "/api/v1"
# Initialize container
container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup
    logger.info("🚀 Starting Global Supply Chain API...")
    
    # Initialize container resources
    await container.init_resources()
    
    # Wire dependency injection and pre-initialize services
    logger.info("🔧 Wiring dependency injection...")
    start_init = time.time()
    
    # Wire all modules that use dependency injection
    container.wire(modules=[
        __name__,
        chat_service,
        team_agent_service, 
        working_memory_service,
        episodic_memory_service,

        development_stream, 
        user_registration, 
        chat_streaming, 
        memory_management,
        health
    ])
    
    logger.info("✅ API startup completed")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Global Supply Chain API...")
    await container.shutdown_resources()
    logger.info("✅ API shutdown completed")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Global Supply Chain API",
    version="1.0.0",
    description="FastAPI backend for global supply chain chat services with real agent streaming",
    debug=False,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(
    development_stream_router,
    prefix=f"{API_PREFIX}/stream-chat/dummy_stream", 
    tags=["Chat"],
)

app.include_router(
    user_registration_router, 
    prefix=f"{API_PREFIX}/update-create/register_user", 
    tags=["Users"],
)
app.include_router(
    chat_streaming_router, 
    prefix=f"{API_PREFIX}/stream-chat/stream",
    tags=["Chat"]
)
app.include_router(
    memory_management_router, 
    prefix=f"{API_PREFIX}/update-create/update_session_data",
    tags=["Sessions"],
)

# Include health endpoints
app.include_router(health_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        timeout_keep_alive=9000,
        workers=1,
        reload=True,
    )
