import uuid
import asyncio
import time
import traceback

from typing import Dict, Any, Tuple
from agno.models.message import Message
from src.services.team_agent_service import TeamAgentService
from src.services.working_memory_service import WorkingMemoryService
from src.services.episodic_memory_service import EpisodicMemoryService
from src.teams.travel_agent_team import TeamAgent, ChatServiceResponseData
from src.utils.schemas import HistoryTuple, History, history_tuple_to_message, ServiceResponse
from agno.media import Image, Audio, Video, File
from src.utils.schemas import History

from pydantic import BaseModel
from loguru import logger

class ChatServiceParams(BaseModel):
        user_id: str
        session_id: str = None
        message_text: str = ""
        attachments: list = None

class ChatServiceEventData(ChatServiceParams):
    task_id: str

    


class ChatService:
    """
    Main chat service that orchestrates team agent and working memory
    """
    
    def __init__(self, team_agent_service:TeamAgentService, working_memory_service:WorkingMemoryService, episodic_memory_service:EpisodicMemoryService):
        self.team_agent_service = team_agent_service
        self.working_memory_service = working_memory_service
        self.episodic_memory_service = episodic_memory_service
    
    async def process_chat_message(
        self,
        params:ChatServiceParams,
    ):
        """
        Process a chat message with full context and history
        
        Args:
            user_id: User identifier
            session_id: Session identifier (generates new if None)
            message_text: User's message text
            attachments: List of attachment objects
            
        Returns:
            Dict containing response data and metadata
        """

        user_id=params.user_id
        session_id=params.session_id
        message_text=params.message_text
        attachments=params.attachments

        self.working_memory_service.user_id=user_id
        self.working_memory_service.session_id=session_id


        # Generate session_id if not provided (new chat)
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            start_time = time.time()
            print(f"⏱️ ChatService: Starting processing at {start_time}")
            
            # 1. Fetch both working memory and episodic memory concurrently
            memory_start = time.time()
            
            # Initialize variables first to avoid scope issues
            history = None
            episodic_context = None
            next_sequence_id = 1  # Default fallback
            
            # Execute both tasks concurrently with error handling
            try:
                logger.info("⏱️ [DIAGNOSTIC] Fetching memory concurrently...")
                
                # Use asyncio.gather for true concurrent execution
                history_task = asyncio.create_task(self.working_memory_service.fetch_recent_history_direct(max_pairs=2))
                
                episodic_context_task = asyncio.create_task(self.episodic_memory_service.search_similar_sessions(
                        user_id=user_id,
                        query_text=message_text,
                        limit=2
                    ))
                # 2. Get next sequence ID for proper message ordering
                next_sequence_id_task = asyncio.create_task(self.working_memory_service.get_next_sequence_id())

                history, episodic_context, next_sequence_id = await asyncio.gather(history_task, episodic_context_task, next_sequence_id_task, return_exceptions=True)
                
                # Handle potential exceptions from individual tasks
                if isinstance(history, Exception):
                    logger.error(f"❌ Error fetching working memory: {history}")
                    history = None
                
                if isinstance(episodic_context, Exception):
                    logger.error(f"❌ Error fetching episodic memory: {episodic_context}")
                    episodic_context = None
                
                if isinstance(next_sequence_id, Exception):
                    logger.error(f"❌ Error fetching next sequence_id: {next_sequence_id}")
                    next_sequence_id = 1

                logger.info("⏱️ [DIAGNOSTIC] Memory fetch completed concurrently")

            except Exception as e:
                logger.error(f"❌ Error during concurrent memory fetch: {e}")
                history = None
                episodic_context = None
                next_sequence_id = 1
            
            memory_end = time.time()
            print(f"⏱️ ChatService: Memory fetch took {memory_end - memory_start:.2f}s")
            
            # 3. Create current message object
            current_message = Message(
                role="user",
                content=message_text,
                images=self._extract_images(attachments) if attachments else None,
                videos=self._extract_videos(attachments) if attachments else None,
                audio=self._extract_audio(attachments) if attachments else None,
                files=self._extract_files(attachments) if attachments else None,
            )
            
            
            # 4. Process message with team agent
            agent_start = time.time()
            print(f"⏱️ ChatService: Starting team agent at {agent_start - start_time:.2f}s")
            
            async for response_data in self.team_agent_service.process_message_with_history(
                user_id=user_id,
                session_id=session_id,
                current_message=current_message,
                history=history,
                episodic_context=episodic_context,
                next_sequence_id=next_sequence_id
            ):
                if response_data.type=='reasoning' or response_data.type=='response':
                    yield response_data
                elif response_data.type=='end':
                    final_response, thinking_response, user_tuple, assistant_tuple=response_data.data

                    # 5. Save both user and assistant messages to database
                    save_success = await self.working_memory_service.save_history_tuples(
                        user_tuple=user_tuple,
                        assistant_tuple=assistant_tuple
                    )
                    
                    # 6. Return response data
                    final_response_data = {
                        "success": True,
                        "session_id": session_id,
                        "user_message": {
                            "sequence_id": user_tuple.sequence_id,
                            "text_content": user_tuple.text_content,
                            "attachments": user_tuple.attachments
                        },
                        "assistant_response": {
                            "sequence_id": assistant_tuple.sequence_id,
                            "text_content": final_response,
                            "reasoning_content": thinking_response
                        },
                        "persistence": {
                            "saved_to_db": save_success,
                            "working_memory_updated": save_success
                        }
                    }

                    yield ChatServiceResponseData(
                        type='end', data=final_response_data
                    )
                    return  # Exit after handling the end response
            
        except Exception as e:
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            print(f"❌ Chat service error: {error_details}")
            yield ChatServiceResponseData( type='error', data= {
                "success": False,
                "error": str(e),
                "session_id": session_id
                }
            )
    
    def _extract_images(self, attachments):
        """Extract image attachments"""
        return [Image(url=att['url']) for att in attachments if att.get('type') == 'image']
    
    def _extract_videos(self, attachments):
        """Extract video attachments"""
        return [Video(url=att['url']) for att in attachments if att.get('type') == 'video']
    
    def _extract_audio(self, attachments):
        """Extract audio attachments"""
        return [Audio(url=att['url']) for att in attachments if att.get('type') == 'audio']
    
    def _extract_files(self, attachments):
        """Extract file attachments"""
        return [File(url=att['url']) for att in attachments if att.get('type') == 'file']