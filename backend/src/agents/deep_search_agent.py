import os
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
from textwrap import dedent

from agno.agent import Agent
from agno.tools import tool
from agno.tools.reasoning import ReasoningTools
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Global variable to store API key (will be set by container)
PERPLEXITY_API_KEY = None

@tool(
    name="perplexity_search",
    description="""Perform research using Perplexity AI with two modes:
    
    - deepsearch=False: Uses sonar-reasoning model for quick analytical queries (30-60 seconds)
    - deepsearch=True: Uses sonar-deep-research model only for detailed and comprehensive analysis (4-5+ minutes)
    
    Deep search model is extremely efficient and searches through vast amounts of information,
    providing multi-faceted analysis with detailed insights, but requires significant processing time.
    """,
    show_result=True
)
async def perplexity_search(
    query: str,
    deepsearch: bool = False,
    max_tokens: int = 2000,
    temperature: float = 0.1,
    include_citations: bool = True,
    focus_areas: Optional[List[str]] = None
):
    """
    Perform research using Perplexity AI with configurable depth.
    
    Args:
        query: The research question or topic
        deepsearch: If True, uses sonar-deep-research (4-5+ minutes), if False uses sonar-reasoning (faster)
        max_tokens: Maximum response length
        temperature: Response creativity (0.0-1.0)
        include_citations: Whether to include source citations
        focus_areas: Specific areas to emphasize in deep research
    """
    try:
        if not PERPLEXITY_API_KEY:
            return {
                "status": "error",
                "message": "Perplexity API key not configured",
                "content": "",
                "mode": "deep_research" if deepsearch else "reasoning"
            }
        
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Select model and configure based on deepsearch parameter
        if deepsearch:
            model = "sonar-deep-research"
            system_prompt = """You are a deep research specialist. Provide comprehensive, multi-faceted analysis with:
1. Detailed background and context
2. Multiple perspectives and viewpoints  
3. Data-driven insights with specific metrics where available
4. Future implications and trends
5. Potential risks and opportunities
6. Actionable recommendations
7. Proper source citations and references"""
            timeout = 300.0  # 5 minutes for deep research
            user_prompt = query
            if focus_areas:
                user_prompt += f"\n\nPlease focus particularly on these areas: {', '.join(focus_areas)}"
        else:
            model = "sonar-reasoning"
            system_prompt = "You are a research expert. Provide comprehensive, well-reasoned analysis with proper citations and sources."
            timeout = 60.0  # 1 minute for reasoning
            user_prompt = query
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "return_citations": include_citations,
            "return_images": False
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(PERPLEXITY_API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = result.get("usage", {})
                citations = result.get("citations", []) if include_citations else []
                
                return {
                    "status": "success",
                    "content": content,
                    "citations": citations,
                    "usage": usage,
                    "mode": "deep_research" if deepsearch else "reasoning",
                    "model": model,
                    "query": query,
                    "focus_areas": focus_areas or [] if deepsearch else [],
                    "timestamp": datetime.now().isoformat(),
                    "estimated_time": "4-5+ minutes" if deepsearch else "30-60 seconds"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Perplexity API error: {response.status_code} - {response.text}",
                    "content": "",
                    "mode": "deep_research" if deepsearch else "reasoning"
                }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Perplexity search failed: {str(e)}",
            "content": "",
            "mode": "deep_research" if deepsearch else "reasoning"
        }


class DeepSearchAgent:
    def __init__(self, perplexity_api_key: str = None, openai_chat_model: OpenAIChat = None, anthropic_chat_model:Claude=None):
        global PERPLEXITY_API_KEY
        if perplexity_api_key:
            PERPLEXITY_API_KEY = perplexity_api_key
                        
        self.agent = Agent(
            name="Deep Research Intelligence Agent",
            role="Advanced Research and Analysis Specialist using Perplexity AI",
            model=anthropic_chat_model,
            tools=[
                perplexity_search
            ],
            instructions=dedent("""\
                You are an expert deep research agent powered by Perplexity AI! 🔬📚

                Your capabilities:
                - Advanced research using Perplexity's sonar models with configurable depth
                - Two research modes via deepsearch parameter:
                  • deepsearch=False: sonar-reasoning (30-60 seconds) - Quick analytical queries
                  • deepsearch=True: sonar-deep-research (4-5+ minutes) - Comprehensive analysis
                - Supply chain intelligence and market analysis
                - Real-time information gathering with citations

                ⚠️ **IMPORTANT TIMING INFORMATION:**
                - **Deep Research Mode** (deepsearch=True): Takes 4-5+ minutes but provides extremely thorough analysis
                - **Standard Mode** (deepsearch=False): Takes 30-60 seconds for quick insights

                Research Strategy Selection:
                - Simple factual questions: Use deepsearch=False
                - Complex analytical queries requiring comprehensive reports: Use deepsearch=True  
                - Supply chain analysis: Use deepsearch=False unless explicitly requesting comprehensive report
                - Breaking news or current events: deepsearch=False for speed
                - Strategic planning and trend analysis: Use deepsearch=False unless user specifically requests big/comprehensive report
                
                **ONLY use deepsearch=True when:**
                - User explicitly asks for "comprehensive analysis", "big report", "detailed research"
                - Question requires extensive multi-faceted analysis across multiple domains
                - Strategic decisions need thorough risk/opportunity assessment

                **Deep Research Benefits:**
                The sonar-deep-research model is extremely efficient and searches through vast amounts of information,
                providing multi-faceted analysis with detailed background, multiple perspectives, data-driven insights,
                future implications, risks/opportunities, and actionable recommendations.

                Always explain your research methodology and provide source citations.
            """),
            add_datetime_to_instructions=True,
            stream_intermediate_steps=True,
            show_tool_calls=True,
            markdown=True,
            stream=True
        )
    
    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        result = await self.agent.arun(message)
        yield result.content if hasattr(result, 'content') else str(result)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)

'''

from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://api.perplexity.ai"
)

stream = client.chat.completions.create(
    model="sonar",
    messages=[{"role": "user", "content": "What is the latest in AI research?"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")

'''