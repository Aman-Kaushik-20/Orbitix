
from fastapi import (
    Depends,
    APIRouter
)
from fastapi.responses import StreamingResponse
import json
import asyncio
from loguru import logger
from src.utils.schemas import ChatRequest

development_stream_router=APIRouter()
API_PREFIX = "/api/v1"

@development_stream_router.post(f"/", description=' Too much cost .... Try this please for testing..'
)
async def dummy_stream(
        request: ChatRequest,
):
    """
    Streams dummy responses from 'dummy_response.json' with a 1-second delay.
    Useful for frontend testing and development without a live model.
    """
    async def generate_dummy_stream():
        try:
            with open('src/utils/dummy_response.json', 'r') as f:
                responses = json.load(f)
            
            for response in responses:
                yield f"data: {json.dumps(response)}\n\n"
                await asyncio.sleep(1)

        except FileNotFoundError:
            logger.error("Could not find dummy_response.json")
            error_response = {
                "type": "error",
                "content": "dummy_response.json not found in the project root."
            }
            yield f"data: {json.dumps(error_response)}\n\n"
        except Exception as e:
            logger.error(f"Error during dummy stream: {e}")
            error_response = {
                "type": "error",
                "content": f"An error occurred: {str(e)}"
            }
            yield f"data: {json.dumps(error_response)}\n\n"

    return StreamingResponse(
        generate_dummy_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
