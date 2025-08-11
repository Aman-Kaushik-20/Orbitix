# Third Party Dependency Imports
from dependency_injector import containers, providers
import asyncpg
import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j._async.driver import AsyncGraphDatabase
from openai import OpenAI
from supabase import create_async_client, AsyncClient
from amadeus import Client as AmadeusClient
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

#Agents
from src.agents.news_agent.news_agent import TravelNewsAgent
from src.agents.deepsearch_agent.deep_search_agent import TravelResearchAgent
from src.agents.amadeus.amadeus_agent import AmadeusAgent
from src.agents.elevenlabs.elevenlabs_agent import ElevenLabsAgent
from src.agents.google_maps.google_maps_agent import GoogleMapsAgent
from src.agents.traveladvisor.travel_advisor_agent import TripAdvisorAgent
from src.agents.elevenlabs.audio_tour_agent import AudioTourAgent

#teams
from src.teams.travel_agent_team import TeamAgent

#providers
from src.providers.voyage_embedder import VoyageEmbeddings

#services
from src.services.user_registration_service import RegisterUser
from src.services.team_agent_service import TeamAgentService
from src.services.working_memory_service import WorkingMemoryService
from src.services.episodic_memory_service import EpisodicMemoryService
from src.services.chat_service import ChatService

# Python Imports
from typing import AsyncGenerator
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')


async def _init_supabase_client(supabase_url: str, supabase_key: str) -> AsyncGenerator[AsyncClient, None]:
    """Async initializer for the Supabase client."""
    client = await create_async_client(supabase_url=supabase_url, supabase_key=supabase_key)
    yield client
    # No explicit close needed for supabase-py v2, but could be added here for other resources.


async def _init_db_pool(db_uri: str) -> AsyncGenerator[asyncpg.Pool, None]:
    """Async initializer for the asyncpg connection pool."""
    pool = await asyncpg.create_pool(
        dsn=db_uri, 
        min_size=2, 
        max_size=10,
        command_timeout=30,
        server_settings={
            'jit': 'off'
        },
        ssl='require',
        statement_cache_size=0  # Disable prepared statements for pgbouncer compatibility
    )
    yield pool
    await pool.close()


class Container(containers.DeclarativeContainer):

    # Environment variables
    voyage_api_key = os.getenv('VOYAGE_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key=os.getenv('CLAUDE_API_KEY')
    perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
    news_api_key = os.getenv('NEWS_API_KEY')
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    amadeus_client_id = os.getenv('AMADEUS_CLIENT_ID')
    amadeus_client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
    supabase_url  = os.getenv("SUPABASE_URL")
    supabase_key  = os.getenv("SUPABASE_KEY")
    postgres_uri = os.getenv("POSTGRES_URI")
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    trip_advisor_api_key = os.getenv('TRIPADVISOR_API_KEY')
    gemini_api_key = os.getenv('GOOGLE_API_KEY')

    # LLM Clients
    openai_client = providers.Singleton(
        OpenAI,
        api_key=openai_api_key
    )


    # Third Party Libararies llm abstraction
    neo4j_ex_llm = providers.Singleton(
        OpenAILLM,
        model_name="gpt-4o-mini",
        model_params={
            "temperature": 0  # turning temperature down for more deterministic results
        }
    )

    amadeus_client=AmadeusClient(
        client_id=amadeus_client_id,
        client_secret=amadeus_client_secret
    )

    openai_chat_model = providers.Singleton(
        OpenAIChat,
        id="gpt-4.1-2025-04-14",
        api_key=openai_api_key,
        temperature=0.2,
        max_tokens=1024,
    )

    anthropic_chat_model = providers.Singleton(
        Claude,
        id="claude-sonnet-4-20250514",
        api_key=anthropic_api_key,
        thinking={"type": "enabled", "budget_tokens": 1024},
        
    )


    # Database Drivers and Clients

    neo4j_driver = providers.Singleton(neo4j.GraphDatabase.driver, neo4j_uri, auth=(neo4j_username, neo4j_password))

    neo4j_async_driver = providers.Singleton(
        AsyncGraphDatabase.driver,
        neo4j_uri,
        auth=(neo4j_username, neo4j_password)
    )

    supabase_client = providers.Resource(
        _init_supabase_client,
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )

    db_pool = providers.Resource(
        _init_db_pool,
        db_uri=postgres_uri
    )


    # Agent Class Objects
    amadeus_agent_class = providers.Singleton(
        AmadeusAgent,
        amadeus_client=amadeus_client,
        openai_chat_model=openai_chat_model,
        anthropic_chat_model=anthropic_chat_model
    )


    elevenlabs_agent_class = providers.Singleton(
        ElevenLabsAgent,
        perplexity_api_key=perplexity_api_key
    )

    news_agent_class = providers.Singleton(
        TravelNewsAgent,
        news_api_key=news_api_key,
        openai_chat_model=openai_chat_model,
        anthropic_chat_model=anthropic_chat_model,
    )
    
    travel_research_agent_class = providers.Singleton(
        TravelResearchAgent,
        perplexity_api_key=perplexity_api_key,
        openai_chat_model=openai_chat_model,
        anthropic_chat_model=anthropic_chat_model,
    )

    google_maps_agent_class = providers.Singleton(
        GoogleMapsAgent,
        google_maps_api_key=google_maps_api_key,
        perplexity_api_key=perplexity_api_key,
        openai_chat_model=openai_chat_model,
    )

    trip_advisor_agent_class = providers.Singleton(
        TripAdvisorAgent,
        trip_advisor_api_key=trip_advisor_api_key,
    )



    # Database Management Service Imports

    voyage_embedder = providers.Singleton(VoyageEmbeddings, api_key=voyage_api_key)


    working_memory_service = providers.Singleton(
        WorkingMemoryService,
        db_pool=db_pool,
        anthropic_chat_model=anthropic_chat_model
        
    )

    episodic_memory_service=providers.Singleton(
        EpisodicMemoryService, 
        db_pool=db_pool,
        voyage_embedder=voyage_embedder,
        supabase_client=supabase_client, # Kept for other potential methods
        working_memory_service=working_memory_service,
        openai_client=openai_client
        )



    team_agent_class=providers.Singleton(
        TeamAgent,
            amadeus_agent_class =amadeus_agent_class, 
            elevenlabs_agent_class=elevenlabs_agent_class , 
            news_agent_class = news_agent_class, 
            travel_research_agent_class = travel_research_agent_class,
            google_maps_agent_class = google_maps_agent_class,
            trip_advisor_agent_class = trip_advisor_agent_class, 
            working_memory_service = working_memory_service, 
            openai_chat_model = openai_chat_model, 
            anthropic_chat_model = anthropic_chat_model, 
            openai_client =  openai_client
    )




    team_agent_service = providers.Singleton(
        TeamAgentService, team_agent_class=team_agent_class,
    )



    chat_service=providers.Singleton(
        ChatService, team_agent_service=team_agent_service, working_memory_service=working_memory_service, episodic_memory_service=episodic_memory_service
    )

    register_user_service=providers.Singleton(
        RegisterUser, db_pool=db_pool,
    )

    audio_tour_agent_class = providers.Singleton(
        AudioTourAgent,
        gemini_api_key=gemini_api_key,
    )



# # In your application's main async function
# container = Container()
# await container.init_resources()

# # ... your application logic ...
# working_memory = await container.working_memory_service()


# # Shutdown resources when the application exits
# await container.shutdown_resources()