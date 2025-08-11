from fastapi import (
    Depends,
    APIRouter
)
from src.core.container import Container
from src.services.chat_service import ChatService, ChatServiceParams
from src.utils.schemas import ChatRequest
from fastapi.responses import StreamingResponse, JSONResponse
from dependency_injector.wiring import Provide, inject
from loguru import logger
import json
import time
import uuid

chat_streaming_router = APIRouter()
API_PREFIX = "/api/v1"

@chat_streaming_router.post("/stream")
@inject
async def stream_chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(Provide[Container.chat_service])
):
    """
    Handles a chat request and streams the response.
    This single endpoint replaces the previous two-step process.
    """
    task_id = str(uuid.uuid4())
    user_id = request.user_id or str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"🚀 Starting chat stream - Task: {task_id}, User: {user_id}, Session: {session_id}")
    
    async def generate_stream():
        try:
            start_time = time.time()
            logger.info(f"⏱️ Stream started at {start_time}")
            
            # Chat service is now injected via dependency injection
            logger.info(f"🔍 Chat service type: {type(chat_service)}")
            
            # Create chat service params
            params = ChatServiceParams(
                user_id=user_id,
                session_id=session_id,
                message_text=request.message,
                attachments=request.attachments
            )
            
            params_created_time = time.time()
            logger.info(f"⏱️ Params created in {params_created_time - start_time:.2f}s")
            
            logger.info(f"🔄 Processing with real agent system - Task: {task_id}")
            
            sequence = 0
            first_token_sent = False
            
            # Stream responses from chat service
            process_start_time = time.time()
            logger.info(f"⏱️ Starting chat service processing at {process_start_time - start_time:.2f}s")
            
            async for response_data in chat_service.process_chat_message(params=params):
                sequence += 1
                
                if not first_token_sent:
                    first_token_time = time.time()
                    logger.info(f"🎉 FIRST TOKEN RECEIVED in {first_token_time - start_time:.2f}s")
                    first_token_sent = True
                
                if response_data.type == 'reasoning':
                    data = {
                        "type": "reasoning",
                        "content": response_data.data,
                        "sequence": sequence,
                        "task_id": task_id
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    
                elif response_data.type == 'response':
                    data = {
                        "type": "response",
                        "content": response_data.data,
                        "sequence": sequence,
                        "task_id": task_id
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    
                elif response_data.type == 'end':
                    # Send final completion
                    completion_data = {
                        "type": "end",
                        "content": "Stream completed successfully",
                        "task_id": task_id,
                        "final_data": response_data.data
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    
                    logger.info(f"✅ Stream completed - Task: {task_id}")
                    break
                    
                elif response_data.type == 'error':
                    error_data = {
                        "type": "error",
                        "content": f"Error: {response_data.data}",
                        "task_id": task_id
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    
                    logger.error(f"❌ Stream error - Task: {task_id}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Stream generation error - Task: {task_id}: {e}")
            error_data = {
                "type": "error",
                "content": f"Internal error: {str(e)}",
                "task_id": task_id
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
