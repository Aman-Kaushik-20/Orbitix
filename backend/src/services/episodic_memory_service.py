import os
from typing import List, Dict, Any
from supabase import create_async_client, AsyncClient
from src.providers.voyage_embedder import VoyageEmbeddings
from src.services.working_memory_service import WorkingMemoryService
from src.utils.schemas import History, HistoryTuple
from src.utils.prompts import get_update_session_data_prompt
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from loguru import logger
import asyncpg
import asyncio
import json

load_dotenv()


# Episodic memory class
class EpisodicMemory(BaseModel):
    session_name:str
    session_tags:List[str]
    what_worked:str
    what_not_worked:str
    what_to_avoid:str
    metadata: str  # Changed from dict to str


class EpisodicSessionSummary(BaseModel):
    session_id: str
    session_name: str
    what_worked: str
    what_not_worked: str
    what_to_avoid: str
    session_tags: List[str]
    message_count: int
    created_at: datetime

class EpisodicMemoryService:
    """Service for episodic memory operations with semantic search"""
    
    def __init__(self, db_pool: asyncpg.Pool, voyage_embedder: VoyageEmbeddings, supabase_client: AsyncClient, working_memory_service:WorkingMemoryService, openai_client:OpenAI):
        self.db_pool = db_pool
        self.voyage_embedder = voyage_embedder
        self.supabase_client = supabase_client
        self.working_memory_service = working_memory_service
        self.openai_client = openai_client

    async def search_similar_sessions(self, user_id: str, query_text: str, limit: int = 2) -> str:
        """
        Search for similar sessions using cosine similarity search
        
        Args:
            user_id: User identifier
            query_text: Current user query to find similar sessions
            limit: Maximum number of similar sessions to return
            
        Returns:
            List of similar session data
        """
        try:
            
            embedding = self.voyage_embedder.embed_query(query_text)
            
            sql_query = """
                SELECT session_name, what_worked, what_not_worked, what_to_avoid
                FROM episodic_similarity_search(
                    search_user_id => $1,
                    query_embedding => $2,
                    match_count => $3
                )
            """
            
            async with self.db_pool.acquire() as connection:
                rows = await connection.fetch(sql_query, user_id, embedding, limit)

            if not rows:
                return "No similar episodic memories found."
            
            formatted_context = "\n\n".join(
                [
                    f"Episodic Memory from Session: \"{row['session_name']}\"\n"
                    f"Session Tags from session: {row['session_tags']}"
                    f"- What worked: {row['what_worked']}\n"
                    f"- What did not work: {row['what_not_worked']}\n"
                    f"- What to avoid: {row['what_to_avoid']}"
                    for row in rows
                ]
            )
            
            return formatted_context
            
        except Exception as e:
            return f"Error searching episodic memory: {e}"
    
    def format_episodic_context(self, similar_sessions: List[EpisodicSessionSummary]) -> str:
        """
        Format episodic memory context for system prompt
        
        Args:
            similar_sessions: List of similar session data
            
        Returns:
            Formatted context string for system prompt
        """
        if not similar_sessions:
            return ""
        
        context_str = "--- EPISODIC MEMORY CONTEXT ---\n\n"
        context_str+="Based on similar past conversations with this user:\n"
        
        for i, session in enumerate(similar_sessions):
            context_str+=f"Session Number : {i+1}\n"
            context_str += f"- Session: {session.session_name} (ID: {session.session_id})\n"
            context_str += f"  - What Worked: {session.what_worked}\n"
            context_str += f"  - What Didn't Work: {session.what_not_worked}\n"
            context_str += f"  - To Avoid: {session.what_to_avoid}\n"
            context_str += f"  - Tags: {', '.join(session.session_tags)}\n"
            context_str += "\n"

        return context_str


    def get_openai_structured_session_data(self, old_session_data:str, complete_history_string:str, response_schema:BaseModel):
        logger.info(f'get_openai_structured_session_data called  !')
        response = self.openai_client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": "You are an expert AI assistant tasked with summarizing conversation histories for an agent's episodic memory."},
                {
                    "role": "user",
                    "content": get_update_session_data_prompt(old_session_data=old_session_data, complete_history_string=complete_history_string),
                },
            ],
            text_format=response_schema,
        )
        logger.info(f'get_openai_structured_session_data completed sucessfully !')

        return response.output_parsed

    async def update_episodic_memory(self, user_id: str, session_id: str) -> 'EpisodicMemory':
        try:

            # 1. Fetch history
            complete_history = await self.working_memory_service.fetch_all_session_history_direct(user_id=user_id, session_id=session_id)
            complete_history_string = complete_history.to_string()

            print('complete_history_string:', complete_history_string)
            # 2. Fetch old data within a transaction
            async with self.db_pool.acquire() as connection:
                async with connection.transaction():
                    old_data_query = '''
                        SELECT session_name, session_tags, what_worked, what_not_worked, what_to_avoid, metadata
                        FROM episodic_memory
                        WHERE user_id = $1 AND session_id = $2
                    '''
                    response = await connection.fetch(old_data_query, user_id, session_id)
                    
                    old_session_data = "No previous session summary exists. Create one from the history."
                    if response:
                        # Fixed string formatting for clarity and correctness
                        row = response[0]
                        metadata_json_str = json.dumps(row['metadata'])
                        # Convert session_tags list to string representation
                        session_tags_str = str(row['session_tags']) if row['session_tags'] else "[]"
                        old_session_data = (
                            f"session_name: {row['session_name']}\n\n"
                            f"session_tags: {session_tags_str}\n\n"
                            f"what_worked: {row['what_worked']}\n\n"
                            f"what_not_worked: {row['what_not_worked']}\n\n"
                            f"what_to_avoid: {row['what_to_avoid']}\n\n"
                            f"metadata: {metadata_json_str}\n\n"
                        )
                    print('old_session_data:', old_session_data)
                    # 3. Run the blocking OpenAI call in a separate thread
                    new_session_data: EpisodicMemory = await asyncio.to_thread(
                        self.get_openai_structured_session_data,
                        old_session_data,
                        complete_history_string,
                        EpisodicMemory
                    )
                    print('new_session_data:', new_session_data)

                    # Convert session_tags list to string for concatenation
                    session_tags_str = ' '.join(new_session_data.session_tags) if isinstance(new_session_data.session_tags, list) else str(new_session_data.session_tags)
                    
                    content=str(new_session_data.session_name + ' ' +
                       session_tags_str + ' ' +
                       new_session_data.what_worked + ' ' +
                       new_session_data.what_not_worked + ' ' +
                       new_session_data.what_to_avoid + ' ' + 
                       new_session_data.metadata)
                    
                    # Get embeddings and convert to PostgreSQL format
                    embeddings_list = self.voyage_embedder.embed_query(content)
                    # Convert to PostgreSQL array string format: '[1.0, 2.0, 3.0]'
                    new_embeddings = '[' + ','.join(map(str, embeddings_list)) + ']'

                    message_count=len(complete_history.history) if complete_history.history else 0
                    
                    # The metadata is already a JSON string from the LLM. No need to parse it.

                    # 4. Upsert the database with the new data (INSERT or UPDATE)
                    upsert_sql_query = '''
                        INSERT INTO episodic_memory (
                            user_id, session_id, session_name, session_tags, 
                            what_worked, what_not_worked, what_to_avoid, 
                            metadata, message_count, content, session_embeddings
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (user_id, session_id) 
                        DO UPDATE SET
                            session_name = EXCLUDED.session_name,
                            session_tags = EXCLUDED.session_tags,
                            what_worked = EXCLUDED.what_worked,
                            what_not_worked = EXCLUDED.what_not_worked,
                            what_to_avoid = EXCLUDED.what_to_avoid,
                            metadata = EXCLUDED.metadata,
                            message_count = EXCLUDED.message_count,
                            content = EXCLUDED.content,
                            session_embeddings = EXCLUDED.session_embeddings,
                            updated_at = NOW()
                    '''
                    
                    await connection.execute(
                       upsert_sql_query, 
                       user_id,        # $1
                       session_id,     # $2  
                       new_session_data.session_name,      # $3
                       new_session_data.session_tags,      # $4
                       new_session_data.what_worked,       # $5
                       new_session_data.what_not_worked,   # $6
                       new_session_data.what_to_avoid,     # $7
                       new_session_data.metadata,          # $8
                       message_count,                      # $9
                       content,                            # $10
                       new_embeddings                      # $11
                    )
            
            # 5. Return the updated data
            return new_session_data

        except Exception as e:
            logger.error(f'Error Occured in Updating Episodic Memory {e}')
            raise # Re-raise the exception to be handled by the caller

        
    