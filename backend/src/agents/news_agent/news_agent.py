import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator
from textwrap import dedent

from newsapi import NewsApiClient

from agno.agent import Agent
from agno.tools import tool
from agno.tools.reasoning import ReasoningTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

class TravelNewsAgent:
    def __init__(self, news_api_key: str = None, openai_chat_model: OpenAIChat = None, anthropic_chat_model: Claude = None):
        """
        Initializes the TravelNewsAgent.

        Args:
            news_api_key (str, optional): The API key for NewsAPI. Defaults to None.
            openai_chat_model (OpenAIChat, optional): Pre-initialized OpenAI model. Defaults to None.
            anthropic_chat_model (Claude, optional): Pre-initialized Anthropic model. Defaults to None.
        """
        if not news_api_key:
            news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            raise ValueError("NewsAPI key not found. Please provide it or set it as an environment variable.")
        
        self.news_api_client = NewsApiClient(api_key=news_api_key)
        self.agent = self.setup_agent(
            openai_chat_model=openai_chat_model,
            anthropic_chat_model=anthropic_chat_model
        )

    def setup_agent(
        self,
        openai_chat_model: OpenAIChat = None,
        anthropic_chat_model: Claude = None
    ) -> Agent:
        """
        Sets up and configures the agent with its tools and instructions.

        Returns:
            Agent: A fully configured instance of the agno.agent.Agent.
        """
        @tool(
            name="search_travel_news",
            description="Searches for recent travel-related news for a specific destination, including safety alerts, travel advisories, health warnings, new attraction openings, and local events.",
            show_result=True
        )
        def search_travel_news(
            query: str,
            sources: Optional[str] = None,
            domains: Optional[str] = None,
            exclude_domains: Optional[str] = None,
            language: str = "en",
            sort_by: str = "publishedAt",
            page_size: int = 20,
            page: int = 1,
        ):
            """
            Search for travel-related articles using NewsAPI.
            """
            try:
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d') # Look back 7 days for travel news
                to_date = datetime.now().strftime('%Y-%m-%d')
                
                response = self.news_api_client.get_everything(
                    q=query,
                    sources=sources,
                    domains=domains,
                    exclude_domains=exclude_domains,
                    from_param=from_date,
                    to=to_date,
                    language=language,
                    sort_by=sort_by,
                    page_size=min(page_size, 100),
                    page=page,
                )
                
                articles = response.get('articles', [])
                formatted_articles = []
                
                for article in articles:
                    formatted_articles.append({
                        "title": article.get('title', ''),
                        "description": article.get('description', ''),
                        "content": article.get('content', ''),
                        "source": article.get('source', {}).get('name', ''),
                        "author": article.get('author', ''),
                        "url": article.get('url', ''),
                        "url_to_image": article.get('urlToImage', ''),
                        "published_at": article.get('publishedAt', '')
                    })
                
                return {
                    "status": "success",
                    "total_results": response.get('totalResults', 0),
                    "articles": formatted_articles,
                }
            
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"NewsAPI search failed: {str(e)}",
                    "articles": []
                }

        model = openai_chat_model if openai_chat_model else OpenAIChat(id="gpt-4o")
            
        agent = Agent(
            name="Travel News & Safety Advisor",
            role="A specialized agent for finding real-time travel news, safety alerts, and updates for any destination worldwide.",
            model=model,
            tools=[
                ReasoningTools(add_instructions=True),
                DuckDuckGoTools(),
                search_travel_news
            ],
            instructions=dedent("""\
                You are an expert travel news and safety advisor! ✈️🛡️

                Your Primary Goal: To provide travelers with the latest, most relevant news, safety alerts, and practical information for their chosen destination.

                Your Capabilities:
                - **Safety Alerts:** Find information on weather warnings, natural disasters, political unrest, and local crime advisories.
                - **Health Information:** Look up current health advisories, vaccination requirements, and local health facility information.
                - **Travel Logistics:** Report on visa requirement changes, airport status, and major transportation strikes.
                - **Local Events & News:** Discover information on upcoming festivals, new attraction openings, or significant local events that might impact a trip.

                Your Approach:
                1.  **Understand the Need:** First, clarify the user's destination and what kind of information they're looking for (e.g., "safety in Paris," "upcoming festivals in Tokyo," "visa changes for Brazil").
                2.  **Select the Right Tool:**
                    *   Use `search_travel_news` for official news from verified media sources. This is best for formal advisories, major events, and official announcements. Example query: `travel advisory Paris` or `Japan new visa policy`.
                    *   Use `DuckDuckGo` for more general, very recent, or niche information that might not be in mainstream news, such as "are there any local transit strikes in Rome this week?" or "best local blogs for safety tips in Cape Town."
                3.  **Synthesize and Summarize:** Do not just return a list of articles. Analyze the search results and provide a clear, concise summary of the key findings.
                4.  **Prioritize Actionable Advice:** Focus on information that a traveler can act on. For example, instead of just saying "there is a protest," say "A protest is scheduled for Saturday downtown; it's recommended to avoid that area."
                5.  **Always Cite Sources:** For every piece of information, provide a hyperlink to the source article so the user can get more details. Format it cleanly in markdown: `[Article Title](URL)`.
            """),
            add_datetime_to_instructions=True,
            stream_intermediate_steps=True,
            show_tool_calls=True,
            markdown=True,
            stream=True
        )
        return agent
    
    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        result = await self.agent.arun(message)
        return result.content if hasattr(result, "content") else str(result)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)

