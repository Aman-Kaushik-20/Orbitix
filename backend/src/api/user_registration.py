from fastapi import (
    Depends,
    APIRouter,
    HTTPException, 
    status as http_status
)
from src.services.user_registration_service import RegisterUser

from dependency_injector.wiring import inject, Provide
from src.core.container import Container
from loguru import logger
from src.utils.schemas import User

user_registration_router=APIRouter()
API_PREFIX = "/api/v1"


@user_registration_router.post(f"/", description="Register New User", status_code=http_status.HTTP_201_CREATED)
@inject
async def register_user(
    user_info: User,
    register_user_service: RegisterUser = Depends(Provide[Container.register_user_service])
):
    try:
        message = await register_user_service.register(user_info)
        return {"status": message}
    except ValueError as e:
        # Catches 'user already exists' and returns a 409 Conflict
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        # Catches any other unexpected error from the service
        logger.error(f"Unhandled exception in register_user endpoint: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while registering the user."
        )
