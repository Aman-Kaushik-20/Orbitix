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

# Global variable to store API key (will be set by container)
NEWS_API_KEY = None

@tool(
    name="search_news_everything",
    description="""Search through millions of articles from 150,000+ news sources using NewsAPI /everything endpoint.
    
    Key parameters:
    - query: Keywords/phrases (use quotes for exact match, + for must include, - for exclude, AND/OR/NOT operators)
    - sources: Comma-separated source identifiers (max 20)
    - domains: Comma-separated domains to include (e.g., bbc.co.uk,techcrunch.com)
    - excludeDomains: Domains to exclude
    - language: 2-letter ISO code (en, fr, de, etc.)
    - sortBy: relevancy, popularity, or publishedAt
    - pageSize: Results per page (max 20)
    
    Returns: Articles with title, description, source, author, url, urlToImage, publishedAt, content (truncated to 200 chars)
    """,
    show_result=True
)
def search_news_everything(
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
    Search for articles using NewsAPI endpoint.
    
    Advanced search features:
    - Exact phrases: Use quotes "supply chain disruption"
    - Must include: +bitcoin +ethereum
    - Must exclude: -speculation
    - Boolean operators: crypto AND (ethereum OR bitcoin) NOT speculation
    """
    try:
        if not NEWS_API_KEY:
            return {
                "status": "error",
                "message": "NewsAPI key not configured",
                "articles": []
            }
        
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        
        # If no date specified, use last day's for everything endpoint
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        to_date=datetime.now().strftime('%Y-%m-%d')
        
        response = newsapi.get_everything(
            q=query,
            sources=sources,
            domains=domains,
            exclude_domains=exclude_domains,
            from_param=from_date,
            to=to_date,
            language=language,
            sort_by=sort_by,
            page_size=min(page_size, 100),  # API max is 100
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
            "query": query,
            "search_params": {
                "sources": sources,
                "domains": domains,
                "exclude_domains": exclude_domains,
                "from_date": from_date,
                "to_date": to_date,
                "language": language,
                "sort_by": sort_by,
                "page_size": page_size,
                "page": page
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"NewsAPI everything search failed: {str(e)}",
            "articles": []
        }



class NewsAgent:
    def __init__(self, news_api_key: str = None, openai_chat_model: OpenAIChat = None, anthropic_chat_model:Claude=None):
        global NEWS_API_KEY
        if news_api_key:
            NEWS_API_KEY = news_api_key
            
        # Use pre-initialized model if provided, otherwise create new one
        model = openai_chat_model if openai_chat_model else OpenAIChat(id="gpt-4o")
            
        self.agent = Agent(
            name="Global News Intelligence Agent",
            role="Real-time News Analysis and Information Gathering Specialist",
            model=model,
            tools=[
                ReasoningTools(add_instructions=True),
                DuckDuckGoTools(),
                search_news_everything
            ],
            instructions=dedent("""\
                You are an expert news intelligence agent specialized in real-time information gathering! 📰🔍

                Your capabilities:
                - Real-time news monitoring and analysis
                - Multi-source news aggregation (NewsAPI Everything + DuckDuckGo)
                - Supply chain and business news expertise
                - Market intelligence and trend analysis
                - Breaking news detection and impact assessment

                Your approach:
                1. Select appropriate search strategies:
                   - NewsAPI Everything for comprehensive news from sources, just gives today's news, no further back
                   - DuckDuckGo for broader web-based news and recent updates, Normal Web-Search
                2. Analyze and synthesize information from multiple sources
                3. Provide context and implications of news developments
                4. Identify trends and patterns in news coverage

                Search Strategy Selection:
                - Comprehensive news coverage: Use News for Latest News for Today's News
                - Real-time web intelligence: Use DuckDuckGo for web based search
                - Source-specific research: Use NewsAPI with source/domain filters

                NewsAPI Everything Advanced Search:
                - Use quotes for exact phrases: "supply chain disruption"
                - Use + for required terms: +inflation +supply +chain
                - Use - to exclude terms: supply chain -crypto
                - Use Boolean operators: (inflation OR recession) AND "supply chain"

                Always provide source attribution and assess information reliability.
            """),
            add_datetime_to_instructions=True,
            stream_intermediate_steps=True,
            show_tool_calls=True,
            markdown=True,
            stream=True
        )
    
    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        return await self.agent.arun(message)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)

