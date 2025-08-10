import uvicorn
import time
from datetime import datetime
from contextlib import asynccontextmanager

import src.services.chat_service as chat_service
import src.services.team_agent_service as team_agent_service
import src.services.working_memory_service as working_memory_service
import src.services.episodic_memory_service as episodic_memory_service


from fastapi import FastAPI, status as http_status, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from typing import List

from src.core.container import Container

from src.api import development_stream, user_registration, chat_streaming, memory_management, health
from src.api.development_stream import development_stream_router
from src.api.user_registration import user_registration_router
from src.api.chat_streaming import chat_streaming_router
from src.api.memory_management import memory_management_router
from src.api.health import health_router
from src.utils.gcs_uploads import upload_to_gcp


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


@app.post(f"{API_PREFIX}/upload", tags=["File Upload"])
async def handle_file_upload(files: List[UploadFile] = File(...)):
    """
    Receives one or more files as multipart/form-data and uploads them to GCP.

    Args:
        files (List[UploadFile]): A list of files sent from the frontend.

    Returns:
        JSONResponse: A JSON object containing a list of uploaded file details.
                      Each item in the list is a dict: {'type': str, 'url': str}
    """
    uploaded_files_data = []

    for file in files:
        try:
            # 1. Read the file content from the UploadFile object
            file_bytes = await file.read()

            # 2. Extract the file extension from the filename
            try:
                extension = file.filename.split('.')[-1].lower()
            except IndexError:
                # Skip this file if it has no extension, or handle as an error
                logger.warning(f"Skipping file '{file.filename}' due to missing extension.")
                continue

            # 3. Determine media type based on file content type
            content_type = file.content_type
            media_type = "file"  # Default type
            if 'image' in content_type:
                media_type = 'image'
            elif 'audio' in content_type:
                media_type = 'audio'
            elif 'video' in content_type:
                media_type = 'video'
            elif 'pdf' in content_type:
                # Your service seems to handle pdfs as 'file' type.
                # If you have a specific 'pdf' type, change this.
                media_type = 'file'


            # 4. Call your existing upload function
            logger.info(f"Uploading file '{file.filename}' to GCP...")
            public_url = upload_to_gcp(data=file_bytes, extension=extension)

            # 5. Append the result to our list
            uploaded_files_data.append({
                "type": media_type,
                "url": public_url,
                "filename": file.filename,  # Add this line
            })

        except Exception as e:
            logger.error(f"Failed to upload file '{file.filename}': {e}", exc_info=True)
            # Depending on desired behavior, you could continue or raise an error for the whole batch
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred during the upload of '{file.filename}': {str(e)}"
            )

    # 6. Return a success response with the list of uploaded file data
    return JSONResponse(
        status_code=200,
        content={"uploaded_files": uploaded_files_data},
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
