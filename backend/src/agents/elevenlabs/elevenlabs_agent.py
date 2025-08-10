import random
import os
import httpx
import asyncio
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
# from agno.tools.eleven_labs import ElevenLabsTools
from elevenlabs_gcp import ElevenLabsTools
from agno.tools import tool

# --- Environment and API Key Setup ---
load_dotenv('backend/.env')

# Perplexity API Key
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


# --- Tools ---
@tool(
    name="perplexity_search",
    description="Performs a web search using Perplexity AI to find real-time information, like historical facts, cultural details, and interesting stories. Use this to gather information before generating audio.",
)
async def perplexity_search(query: str):
    """
    Perform a quick web search using Perplexity's sonar-reasoning model.
    """
    if not PERPLEXITY_API_KEY:
        return {"error": "Perplexity API key not configured"}

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
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
# List of voices for storytelling. A voice is chosen randomly for each run.
# The voice '21m00Tcm4TlvDq8ikWAM' is multilingual.
voices = [
    # {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (multilingual)"},
    {"id": "EiNlNiXeDU1pqqOPrYMO", "name": "John Doe - Deep"},
    {"id": "EkK5I93UQWFDigLMpZcX", "name": "James - Husky & Engaging"},
    {"id": "NOpBlnGInO9m6vDvFkFC", "name": "Grandpa Spuds Oxley"},
]
selected_voice = random.choice(voices)


# --- Agent Definition ---
audio_agent = Agent(
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
        "4. **Response:** Return the URL of the generated audio file. Do not use markdown.",
    ],
    markdown=True,
    show_tool_calls=True,
)


# --- Main Execution ---
async def main():
    """Asynchronous function to set up and run the agent."""
    prompt = "Generate a small  text to speech audio for  alexander the great..."

    print(f"--- User Prompt ---\n{prompt}\n")
    print(f"--- Voice Selected ---\n{selected_voice['name']} (ID: {selected_voice['id']})\n")
    print("--- Agent Running ---")

    try:
        result = await audio_agent.arun(prompt)
        print("\n--- Agent Response ---")
        # The final result is an object, we access its content
        final_response = result.content if hasattr(result, "content") else str(result)
        print(final_response)
    except Exception as e:
        print(f"\nAn error occurred during agent execution: {e}")
    finally:
        print("\n--- Agent Run Finished ---")


if __name__ == "__main__":
    # Switched to asyncio.run() to support the async perplexity_search tool.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent run interrupted by user.")