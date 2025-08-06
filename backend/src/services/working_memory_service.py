import os
from typing import List, Optional, Tuple
from supabase import create_async_client, AsyncClient
from src.utils.schemas import HistoryTuple, History
from dotenv import load_dotenv
import time
import json
from supabase import AsyncClient
from loguru import logger
from typing import List, Dict, Any
import asyncpg
from src.utils.schemas import Role
from agno.agent import Agent
from agno.tools import tool
from agno.models.anthropic import Claude
from textwrap import dedent



load_dotenv()

class WorkingMemoryService:
    """Service for working memory database operations"""
    
    def __init__(self, db_pool: asyncpg.Pool, anthropic_chat_model:Claude = None):
        self.db_pool = db_pool
        self.user_id=None   # Will set up this in chat_service.py after i get user's request
        self.session_id=None
        self.anthropic_chat_model=anthropic_chat_model
        self.setup_agent()
    
    async def fetch_recent_history_direct(self, max_pairs: int) -> str:
        """Direct method for fetching recent history (not a tool)"""
        limit = max_pairs * 2
        
        logger.info(f"Fetching last {limit} messages for user {self.user_id}, session {self.session_id}")
        
        sql_query = """
            SELECT sequence_id, role, text_content, reasoning_content, attachments
            FROM working_memory
            WHERE user_id = $1 AND session_id = $2
            ORDER BY sequence_id DESC
            LIMIT $3
        """
        
        try:
            async with self.db_pool.acquire() as connection:
                rows = await connection.fetch(sql_query, self.user_id, self.session_id, limit)
            
            if not rows:
                logger.info("No recent history found.")
                return History(history=[]).to_string()
            
            # Convert rows to HistoryTuple objects (reverse to get chronological order)
            history_tuples = []
            for row in reversed(rows):
                # Parse JSON attachments if it's a string, otherwise use as-is
                attachments = row['attachments']
                if isinstance(attachments, str):
                    try:
                        attachments = json.loads(attachments)
                    except (json.JSONDecodeError, TypeError):
                        attachments = []
                elif attachments is None:
                    attachments = []
                
                history_tuple = HistoryTuple(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    sequence_id=row['sequence_id'],
                    role=Role(row['role']),
                    text_content=row['text_content'],
                    reasoning_content=row['reasoning_content'],
                    attachments=attachments
                )
                history_tuples.append(history_tuple)
            
            logger.info(f"Successfully fetched {len(history_tuples)} history entries.")
            return History(history=history_tuples).to_string()

        except Exception as e:
            logger.error(f"❌ Could not fetch working memory for user {self.user_id}, session {self.session_id}: {e}")
            return History(history=[]).to_string()

    @tool(
        name="fetch_recent_history",
        description="Get the Recent history for the current session"
    )
    async def fetch_recent_history(self, max_pairs: int) -> str:
        """
        Fetches the most recent user-assistant message pairs from the conversation history.
        Tool wrapper that calls the direct method.
        """
        return await self.fetch_recent_history_direct(max_pairs)



    async def fetch_all_session_history_direct(self, user_id: str = None, session_id: str = None) -> History:
        """Direct method for fetching all session history (not a tool)"""
        # Use provided parameters or fall back to instance variables
        user_id = user_id or self.user_id
        session_id = session_id or self.session_id
        
        logger.info(f"Fetching all session history for user {user_id}, session {session_id}")
        
        sql_query = """
            SELECT sequence_id, role, text_content, reasoning_content, attachments
            FROM working_memory
            WHERE user_id = $1 AND session_id = $2
            ORDER BY sequence_id ASC
        """
        
        try:
            async with self.db_pool.acquire() as connection:
                rows = await connection.fetch(sql_query, user_id, session_id)
            
            if not rows:
                logger.info("No session history found.")
                return History(history=[])
            
            # Convert rows to HistoryTuple objects
            history_tuples = []
            for row in rows:
                # Parse JSON attachments if it's a string, otherwise use as-is
                attachments = row['attachments']
                if isinstance(attachments, str):
                    try:
                        attachments = json.loads(attachments)
                    except (json.JSONDecodeError, TypeError):
                        attachments = []
                elif attachments is None:
                    attachments = []
                
                history_tuple = HistoryTuple(
                    user_id=user_id,
                    session_id=session_id,
                    sequence_id=row['sequence_id'],
                    role=Role(row['role']),
                    text_content=row['text_content'],
                    reasoning_content=row['reasoning_content'],
                    attachments=attachments
                )
                history_tuples.append(history_tuple)
            
            logger.info(f"Successfully fetched {len(history_tuples)} session history entries.")
            return History(history=history_tuples)

        except Exception as e:
            logger.error(f"❌ Could not fetch session history for user {user_id}, session {session_id}: {e}")
            return History(history=[])

    @tool(
        name="fetch_all_session_history",
        description="Get All of the history for the current session"
    )
    async def fetch_all_session_history(self,) -> str:
        """
        Tool wrapper that calls the direct method and returns string format.
        """
        history = await self.fetch_all_session_history_direct()
        return history.to_string()



    def setup_agent(self,):
        self.agent=Agent(
            name='Session History Agent',
            model=self.anthropic_chat_model,
            tools=[
                self.fetch_recent_history, 
                self.fetch_all_session_history
                ],
            instructions=dedent(
                '''
                You are a specialized AI agent responsible for accessing and retrieving conversation histories.
                Your primary purpose is to provide accurate historical data to other parts of the system.

                - **Always use the available tools** to fetch data when asked.
                - When a user asks for "recent" or "latest" parts of a conversation, use the `fetch_recent_history` tool.
                - When a user needs the "full", "complete", or "entire" conversation, use the `fetch_all_session_history` tool.
                - Pay close attention to the `max_pairs` parameter for `fetch_recent_history` if the user specifies a number.
                '''
            ),
            # stream_intermediate_steps=True,
            # stream=True,
            # reasoning=True,
            show_tool_calls=True,
            markdown=True,

        )



    async def save_history_tuples(
        self, 
        user_tuple: HistoryTuple, 
        assistant_tuple: HistoryTuple
    ) -> bool:
        """
        Save user and assistant message tuples to database using direct SQL
        
        Args:
            user_tuple: User message tuple
            assistant_tuple: Assistant response tuple
            
        Returns:
            True if successful, False otherwise
        """
        
        sql_query = """
            INSERT INTO working_memory (
                user_id, session_id, sequence_id, role, text_content, 
                reasoning_content, attachments
            ) VALUES 
                ($1, $2, $3, $4, $5, $6, $7),
                ($8, $9, $10, $11, $12, $13, $14)
        """
        
        try:
            async with self.db_pool.acquire() as connection:
                await connection.execute(
                    sql_query,
                    # User tuple values
                    user_tuple.user_id,
                    user_tuple.session_id,
                    user_tuple.sequence_id,
                    user_tuple.role.value,
                    user_tuple.text_content,
                    user_tuple.reasoning_content,
                    json.dumps([att.model_dump() for att in user_tuple.attachments] if user_tuple.attachments else []),
                    # Assistant tuple values
                    assistant_tuple.user_id,
                    assistant_tuple.session_id,
                    assistant_tuple.sequence_id,
                    assistant_tuple.role.value,
                    assistant_tuple.text_content,
                    assistant_tuple.reasoning_content,
                    json.dumps([att.model_dump() for att in assistant_tuple.attachments] if assistant_tuple.attachments else [])
                )
            
            logger.info(f"Successfully saved history tuples for session {user_tuple.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving history tuples: {e}")
            return False
    
    async def get_next_sequence_id(self,) -> int:
        """Get the next sequence ID for a session"""
        sql_query = """
            SELECT COALESCE(MAX(sequence_id), 0) + 1 as next_id
            FROM working_memory
            WHERE user_id = $1 AND session_id = $2
        """
        '''
        The COALESCE function returns the first non-null value it is given.
        Case 1 (Existing Session): If the session already has messages, MAX(sequence_id) will return a number (e.g., 5). COALESCE will return that number.
        Case 2 (New Session): If the session has no messages yet, MAX(sequence_id) will return NULL. In this situation, COALESCE will fall back to its second argument, 0, and return 0.
        .. + 1
        '''
        try:
            async with self.db_pool.acquire() as connection:
                result = await connection.fetchrow(sql_query, self.user_id, self.session_id)
                return result['next_id'] if result else 1
        except Exception as e:
            logger.error(f"❌ Error getting next sequence ID: {e}")
            return 1