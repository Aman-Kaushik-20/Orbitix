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

class TravelResearchAgent:
    def __init__(self, perplexity_api_key: str = None, openai_chat_model: OpenAIChat = None, anthropic_chat_model:Claude=None):
        self.agent = self.setup_agent(
            perplexity_api_key=perplexity_api_key,
            anthropic_chat_model=anthropic_chat_model,
            openai_chat_model=openai_chat_model
        )

    def setup_agent(
        self,
        perplexity_api_key: str,
        anthropic_chat_model: Claude = None,
        openai_chat_model: OpenAIChat = None
    ) -> Agent:
        """
        Sets up and configures the Travel Research Agent.

        Args:
            perplexity_api_key: The API key for Perplexity AI.
            anthropic_chat_model: An instance of the Anthropic chat model.
            openai_chat_model: An instance of the OpenAI chat model.

        Returns:
            An configured instance of the agno.agent.Agent.
        """

        @tool(
            name="travel_research",
            description="""Performs travel research using Perplexity AI for trip planning and answering travel-related queries. It has two modes:
        
            - deepsearch=False: For quick questions about a location, such as local prices, best time to visit, operating hours of a place, or recent news. (30-60 seconds)
            - deepsearch=True: For creating comprehensive travel itineraries, researching culture, history, adventure activities, and finding insights from personal travel blogs, articles, and videos. (4-5+ minutes)
        
            This tool can research anything from historical events, cultural norms, monument details, adventure activities (trekking, camping), to local prices and budget information. It prioritizes real-life experiences from other travelers.
            """,
            show_result=True
        )
        async def travel_research(
            query: str,
            deepsearch: bool = False,
            max_tokens: int = 2000,
            temperature: float = 0.1,
            include_citations: bool = True,
            focus_areas: Optional[List[str]] = None
        ):
            """
            Performs in-depth travel research using Perplexity AI.
            
            Args:
                query: The travel-related research question or topic (e.g., "10-day itinerary for Japan", "best street food in Mexico City").
                deepsearch: If True, performs a comprehensive search for detailed trip planning. If False, performs a quick search for specific facts.
                max_tokens: Maximum response length.
                temperature: Response creativity (0.0-1.0).
                include_citations: Whether to include source citations.
                focus_areas: Specific aspects of the trip to focus on (e.g., "food", "history", "adventure").
            """
            try:
                if not perplexity_api_key:
                    return {
                        "status": "error",
                        "message": "Perplexity API key not configured",
                        "content": "",
                        "mode": "deep_research" if deepsearch else "reasoning"
                    }
                
                headers = {
                    "Authorization": f"Bearer {perplexity_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Select model and configure based on deepsearch parameter
                if deepsearch:
                    model = "sonar-deep-research"
                    system_prompt = """You are an expert travel researcher creating a detailed and inspiring travel guide. Your response must be comprehensive and based on deep research of the web, including personal travel blogs, articles, and YouTube videos to capture real-life experiences.
        Your research should include:
        1.  **Detailed Itinerary:** A day-by-day plan with specific places, activities, and suggested timings.
        2.  **Cultural & Historical Context:** Insights into local culture, history, and etiquette.
        3.  **Activities & Experiences:** Information on adventure activities, trekking, camping, local workshops, etc.
        4.  **Food & Drink:** Recommendations for local cuisine, famous restaurants, and street food.
        5.  **Logistics & Budget:** Tips on transportation, accommodation, and estimated local prices for budgeting.
        6.  **Real-World Tips:** Practical advice from other travelers. Prioritize information from personal travel accounts.
        7.  **Citations:** Provide sources for all information."""
                    timeout = 300.0  # 5 minutes for deep research
                    user_prompt = query
                    if focus_areas:
                        user_prompt += f"\n\nPlease focus particularly on these areas: {', '.join(focus_areas)}"
                else:
                    model = "sonar-reasoning"
                    system_prompt = "You are a helpful travel assistant. Provide a clear, concise, and accurate answer to the user's travel-related question. If prices or times are requested, try to find the most current information available and include citations."
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

        agent = Agent(
            name="Expert Travel Research Agent",
            role="A specialized travel planning assistant that uses Perplexity AI to create detailed itineraries and answer any travel-related questions.",
            model=anthropic_chat_model,
            tools=[
                travel_research
            ],
            instructions=dedent("""\
                You are an expert travel research agent powered by Perplexity AI! ✈️🌍

                Your mission is to help users plan amazing trips by providing detailed, well-researched information.

                **Your Primary Tool: `travel_research`**
                This tool has two modes for different types of requests:

                1.  **Quick Search (`deepsearch=False`):**
                    - **Use For:** Simple, factual questions.
                    - **Examples:** "What are the visa requirements for Brazil?", "How much does a metro ticket cost in Tokyo?", "What are some recent events in London?", "Tell me about the history of the Colosseum."
                    - **Response Time:** Fast (30-60 seconds).

                2.  **Comprehensive Research (`deepsearch=True`):**
                    - **Use For:** Complex requests requiring a full travel plan or deep dive.
                    - **Examples:** "Plan a 7-day adventure trip to Costa Rica.", "Give me a detailed historical and cultural guide to Kyoto.", "Create a budget-friendly 2-week backpacking itinerary for Vietnam."
                    - **Response Time:** Slow (4-5+ minutes). Be patient, the result is worth it!

                **CRITICAL GUIDELINES:**
                - **Prioritize Real Experiences:** When building itineraries, your research MUST prioritize information from personal travel blogs, trip reports on forums (like Reddit), and YouTube travel vlogs. This ensures the advice is practical and based on real-world experience.
                - **Be Methodical:** For itinerary requests, use `deepsearch=True`. For simple questions, use `deepsearch=False`. Do not use deep search for simple questions.
                - **Explain Your Process:** Inform the user when you are starting a comprehensive search, as it will take time. For example: "I'm starting a deep research dive to build your custom itinerary. This will take about 4-5 minutes, but I'll come back with a detailed plan!"
                - **Cover All Angles:** Your research can include history, culture, adventure activities (like trekking, camping), food, local prices, recent news, and information about specific landmarks or people.
                - **Include Citations:** Always provide source citations for the information you find.
                - **Proper Formatting:** All responses must be properly and prettily formatted in markdown. For example:
                  - **Hyperlinks:** `[Link Text](https://example.com)`
                  - **Images:** `![Alt Text](https://example.com/image.png)`
                  - **Videos:** To embed a video player, use the HTML5 `<video>` tag: `<video controls src="https://example.com/video.mp4" title="Video Title"></video>`
                  - **Audio:** To embed an audio player, use the HTML5 `<audio>` tag: `<audio controls src="https://example.com/audio.mp3" title="Audio Title"></audio>`
                  - **Note on Media:** The markdown renderer must support HTML tags for the players to appear. If a direct embed is not possible (e.g., for YouTube videos), provide a clear, descriptive hyperlink to the content as a fallback.
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