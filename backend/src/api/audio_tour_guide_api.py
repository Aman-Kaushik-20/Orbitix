from fastapi import (
    Depends, APIRouter, HTTPException, status
)
from fastapi.responses import StreamingResponse
import json
from typing import List, Dict, Optional
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide
from src.core.container import Container
from src.agents.elevenlabs.audio_tour_agent import AudioTourAgent, AudioTourAgentParams
from loguru import logger

gemini_audio_agent_router = APIRouter()


@gemini_audio_agent_router.post('/')
@inject
async def stream_audio_tour_agent(
    request: AudioTourAgentParams,
    audio_tour_agent_class : AudioTourAgent = Depends(Provide[Container.audio_tour_agent_class]),
) -> StreamingResponse:
    """
    Streams the response from the AudioTourAgent in Server-Sent Events (SSE) format.
    """
    async def event_generator():
        try:
            text_message = request.text_message
            attachments = request.attachments

            logger.info(f'Received Attachments : {attachments}')
            
            logger.info(f"Received request for audio tour. Message: '{text_message}', Attachments: {len(attachments) if attachments else 0}")
            
            audio_tour_stream = audio_tour_agent_class.run_async(request)

            async for event in audio_tour_stream:
                # Format as Server-Sent Event (SSE)
                yield f"{json.dumps(event)}"
                
        except Exception as e:
            logger.error(f"Error during audio tour generation: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "data": f"An error occurred during audio generation: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )