import random
import os
import httpx
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
# from agno.tools.eleven_labs import ElevenLabsTools
from src.agents.elevenlabs.elevenlabs_toolkit import ElevenLabsTools
from agno.tools import tool

# --- Environment and API Key Setup ---
load_dotenv('backend/.env')

# Perplexity API URL
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class ElevenLabsAgent:
    def __init__(self, perplexity_api_key: str):
        """
        Initializes the ElevenLabsAgent.

        Args:
            perplexity_api_key (str): The API key for Perplexity AI.
        """
        self.agent = self.setup_agent(perplexity_api_key=perplexity_api_key)

    def setup_agent(self, perplexity_api_key: str) -> Agent:
        """
        Sets up and configures the agent with its tools and instructions.

        Args:
            perplexity_api_key (str): The API key for Perplexity AI.

        Returns:
            Agent: A fully configured instance of the agno.agent.Agent.
        """
        @tool(
            name="perplexity_search",
            description="Performs a web search using Perplexity AI to find real-time information, like historical facts, cultural details, and interesting stories. Use this to gather information before generating audio.",
        )
        async def perplexity_search(query: str):
            """
            Perform a quick web search using Perplexity's sonar-reasoning model.
            """
            if not perplexity_api_key:
                return {"error": "Perplexity API key not configured"}

            headers = {
                "Authorization": f"Bearer {perplexity_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "sonar-reasoning",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides concise and factual information for creating engaging audio scripts.",
                    },
                    {"role": "user", "content": query},
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
            }

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(PERPLEXITY_API_URL, json=payload, headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {"status": "success", "content": content}
                    else:
                        return {
                            "error": f"Perplexity API error: {response.status_code} - {response.text}"
                        }
            except Exception as e:
                return {"error": f"Perplexity search failed: {e}"}

        # --- Voice Selection ---
        voices = [
            {"id": "EiNlNiXeDU1pqqOPrYMO", "name": "John Doe - Deep"},
            {"id": "EkK5I93UQWFDigLMpZcX", "name": "James - Husky & Engaging"},
            {"id": "NOpBlnGInO9m6vDvFkFC", "name": "Grandpa Spuds Oxley"},
        ]
        selected_voice = random.choice(voices)

        # --- Agent Definition ---
        agent = Agent(
            name = 'Eleven Labs Audio Agent',
            model=OpenAIChat(id="gpt-4o"),
            tools=[
                ElevenLabsTools(
                    voice_id=selected_voice["id"],
                    model_id="eleven_multilingual_v2",
                    target_directory="audio_generations",
                ),
                perplexity_search,
            ],
            description="You are a Travel Guide AI assistant, which helps foreigners and travellers make learning interesting and exciting with voices.",
            instructions=[
                "You are an AI travel guide. Your main goal is to produce cinematic and engaging audio stories about historical places, cultural topics, and more.",
                "**Workflow:**",
                "1. **Research:** When a user asks for audio, you MUST first use the `perplexity_search` tool to research the topic. Gather details about its history, cool facts, construction, cultural significance, local folktales, and archaeological findings. When Asked about any Person...find about its biography, related history, facts and figures acc. to that person and context only",
                "2. **Scripting:** From your research, write a well-structured, cinematic script. It should be captivating and educational, not a dry, bookish report. Make it interesting enough to keep listeners engaged.",
                "3. **Audio Generation:** Use the `generate_audio` tool to convert your script into speech.",
                "4. **Response:** Return the URL of the generated audio file embedded in an HTML audio player. For example: `<audio controls src=\"URL_HERE\" title=\"Generated Audio\"></audio>`  to be propley rendered in markdown",
            ],
            markdown=True,
            show_tool_calls=True,
        )
        return agent

    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        result = await self.agent.arun(message)
        return result.content if hasattr(result, 'content') else str(result)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)





if __name__ == "__main__":
    try:

        async def main():
            """Asynchronous function to set up and run the agent."""
            perplexity_key = os.getenv("PERPLEXITY_API_KEY")
            if not perplexity_key:
                print("Error: PERPLEXITY_API_KEY not found in .env file.")
                return

            agent_instance = ElevenLabsAgent(perplexity_api_key=perplexity_key)
            
            prompt = "Generate a small text to speech audio for alexander the great..."

            print(f"--- User Prompt ---\n{prompt}\n")
            print("--- Agent Running ---")

            try:
                final_response = await agent_instance.run_async(prompt)
                print("\n--- Agent Response ---")
                print(final_response)
            except Exception as e:
                print(f"\nAn error occurred during agent execution: {e}")
            finally:
                print("\n--- Agent Run Finished ---")

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent run interrupted by user.")