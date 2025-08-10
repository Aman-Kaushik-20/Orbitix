from typing import Tuple
from agno.models.message import Message
from src.utils.schemas import History, HistoryTuple, history_tuple_to_message, get_latest_history_string
from src.teams.travel_agent_team import TeamAgent, ChatServiceResponseData
from src.utils.schemas import MediaAttachment, MediaContent
import os


class TeamAgentService:
    """Service wrapper for TeamAgent with history management"""
    
    def __init__(self, team_agent_class: TeamAgent):
        self.team_agent_class = team_agent_class
    
    async def process_message_with_history(
        self,
        user_id: str,
        session_id: str,
        current_message: Message,
        history: str = None,
        episodic_context: str = None,
        next_sequence_id: int = 1
    ):
        """
        Process a message with conversation history context
        
        Args:
            user_id: User identifier
            session_id: Session identifier  
            current_message: The new user message
            history: Previous conversation history
            episodic_context: Formatted episodic memory context
            
        Returns:
            Tuple of (final_response, thinking_response, user_tuple, assistant_tuple)
        """
        
        
        # Run the team agent with combined context
        async for response_data in  self.team_agent_class.arun_team_intermediate_steps(
            session_id=session_id,
            user_id=user_id,
            current_message=current_message,
            history_string=history,
            episodic_context=episodic_context
        ):
            if response_data.type=='reasoning' or response_data.type=='response':
                yield response_data
            
            elif response_data.type == 'end':
                final_response, thinking_response=response_data.data

                # Create assistant response tuple
                assistant_tuple = HistoryTuple(
                    user_id=user_id,
                    session_id=session_id,
                    sequence_id=next_sequence_id + 1,
                    role="assistant",
                    text_content=final_response,
                    reasoning_content=thinking_response,
                    attachments=None
                )
                # Use the provided next_sequence_id (calculated from database)
                
                # Create user history tuple for the new message
                user_tuple = HistoryTuple(
                    user_id=user_id,
                    session_id=session_id,
                    sequence_id=next_sequence_id,
                    role="user",
                    text_content=current_message.content,
                    reasoning_content=None,
                    attachments=self._extract_attachments_from_message(current_message)
                )

                yield ChatServiceResponseData( type='end', data=(final_response, thinking_response, user_tuple, assistant_tuple))
    
    def _extract_attachments_from_message(self, message: Message) -> list:
        """Extract attachments from Message object and convert to MediaAttachment format"""        
        attachments = []
        
        # Extract images
        if message.images:
            for img in message.images:
                attachments.append(MediaAttachment(type=MediaContent.IMAGE, url=img.url))
        
        # Extract videos  
        if message.videos:
            for video in message.videos:
                attachments.append(MediaAttachment(type=MediaContent.VIDEO, url=video.url))
        
        # Extract audio
        if message.audio:
            for audio in message.audio:
                attachments.append(MediaAttachment(type=MediaContent.AUDIO, url=audio.url))
        
        # Extract files
        if message.files:
            for file in message.files:
                attachments.append(MediaAttachment(type=MediaContent.FILE, url=file.url))
        
        return attachments if attachments else None