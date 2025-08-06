from fastapi import (
    APIRouter,
    Depends,
    status as http_status
    
)
from src.services.episodic_memory_service import EpisodicMemory, EpisodicMemoryService
from fastapi.responses import  JSONResponse
from src.core.container import Container
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide
from loguru import logger

memory_management_router = APIRouter()
API_PREFIX = "/api/v1"


class UpdateSessionRequest(BaseModel):
    user_id: str
    session_id: str


@memory_management_router.post(f'/', 
          description="Update Session Data based on new Conversations.")
@inject
async def update_session_data(
    request: UpdateSessionRequest,
    episodic_memory_service: EpisodicMemoryService = Depends(Provide[Container.episodic_memory_service])
):
    try:
        updated_session_data = await episodic_memory_service.update_episodic_memory(
            user_id=request.user_id, 
            session_id=request.session_id
        )
        # On success, return a dictionary with a 'message' key
        return {"message": updated_session_data}
    except Exception as e:
        logger.error(f"Failed to update session data for user {request.user_id}, session {request.session_id}: {e}")
        # On failure, return a JSONResponse with a custom 'error' body and status code
        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An internal error occurred while updating the session data."}
        )