import os
import googlemaps
import httpx
import asyncio
from dotenv import load_dotenv
from textwrap import dedent
from typing import AsyncGenerator, Optional, List
from datetime import datetime

from agno.agent import Agent
from agno.tools import tool
from agno.models.openai import OpenAIChat

# --- Environment and API Key Setup ---

# Correctly locate the .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()

# Google Maps API Key
gmaps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if not gmaps_api_key:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file.")
gmaps = googlemaps.Client(key=gmaps_api_key)

# Perplexity API Key
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


# --- Tools for the Agent ---

@tool(
    name="get_travel_recommendation",
    description="Gets travel distance and duration from Google Maps and recommends 'walking' if the distance is very short (<400m), otherwise recommends 'driving'."
)
def get_travel_recommendation(source: str, destination: str):
    """
    Checks both walking and driving routes and provides a recommendation.
    """
    try:
        # First, check the walking distance
        walking_matrix = gmaps.distance_matrix(source, destination, mode='walking')
        if walking_matrix['status'] != 'OK' or walking_matrix['rows'][0]['elements'][0]['status'] != 'OK':
             return {"error": f"Could not retrieve walking distance. Status: {walking_matrix['rows'][0]['elements'][0].get('status', 'UNKNOWN')}"}

        walking_element = walking_matrix['rows'][0]['elements'][0]
        walking_distance_meters = walking_element['distance']['value']

        # Decision logic: recommend walking if < 400 meters
        if walking_distance_meters < 400:
            return {
                "recommendation": "walking",
                "distance": walking_element['distance']['text'],
                "duration": walking_element['duration']['text']
            }
        else:
            # If walking is too far, get driving info
            driving_matrix = gmaps.distance_matrix(source, destination, mode='driving')
            if driving_matrix['status'] != 'OK' or driving_matrix['rows'][0]['elements'][0]['status'] != 'OK':
                return {"error": f"Could not retrieve driving distance. Status: {driving_matrix['rows'][0]['elements'][0].get('status', 'UNKNOWN')}"}
            
            driving_element = driving_matrix['rows'][0]['elements'][0]
            return {
                "recommendation": "driving",
                "distance_text": driving_element['distance']['text'],
                "distance_km": driving_element['distance']['value'] / 1000,
                "duration": driving_element['duration']['text']
            }

    except googlemaps.exceptions.ApiError as e:
        return {"error": f"A Google Maps API error occurred: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}


@tool(
    name="calculate_driving_cost",
    description="Calculates the estimated cost of a driving trip based on distance and fuel price."
)
def calculate_driving_cost(
    distance_km: float, 
    fuel_price_per_liter: float, 
    vehicle_efficiency_kmpl: float = 15.0, 
    apply_fuel_markup: bool = False, 
    additional_flat_fee: float = 0.0
):
    """
    Calculates driving cost from pre-fetched data. Does not call any APIs.
    """
    try:
            final_fuel_price = fuel_price_per_liter * 1.10 if apply_fuel_markup else fuel_price_per_liter
            fuel_needed_liters = distance_km / vehicle_efficiency_kmpl
            estimated_fuel_cost = fuel_needed_liters * final_fuel_price
            total_cost = estimated_fuel_cost + additional_flat_fee

            return {
                'total_estimated_cost': round(total_cost, 2),
                'cost_breakdown': {
                    'base_fuel_cost': round(estimated_fuel_cost, 2),
                    'additional_fee': round(additional_flat_fee, 2),
                    'fuel_price_used': round(final_fuel_price, 2),
                    'fuel_markup_applied': apply_fuel_markup
                }
            }
    except Exception as e:
        return {"error": f"Failed to calculate cost: {e}"}


@tool(
    name="perplexity_search",
    description="Performs a web search using Perplexity AI to find real-time information, like local fuel prices. Use this to get data needed for other tools."
)
async def perplexity_search(query: str):
    """
    Perform a quick web search using Perplexity's sonar-reasoning model.
    """
    if not PERPLEXITY_API_KEY:
        return {"error": "Perplexity API key not configured"}
    
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "sonar-reasoning",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that provides concise and factual information. If asked for a price, find the numerical value and the currency."},
            {"role": "user", "content": query}
        ],
        "max_tokens": 500,
        "temperature": 0.1,
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(PERPLEXITY_API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"status": "success", "content": content}
            else:
                    return {"error": f"Perplexity API error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Perplexity search failed: {e}"}


# --- The Agent ---

class GoogleMapsAgent:
    def __init__(self, chat_model: OpenAIChat):
        self.agent = Agent(
            name="Autonomous Travel Assistant",
            role="An intelligent assistant that recommends travel modes and calculates driving costs automatically.",
            model=chat_model,
            tools=[get_travel_recommendation, calculate_driving_cost, perplexity_search],
            instructions=dedent("""\
                You are a smart travel assistant. Your goal is to help users by figuring out the best mode of transport and, if driving, the estimated cost.

                **Your Autonomous Workflow:**
                1.  **Start:** Begin by asking the user for their **source** and **destination**.
                
                2.  **Get Recommendation:** Use the `get_travel_recommendation` tool with the source and destination. This tool will tell you whether to recommend 'walking' or 'driving'.
                
                3.  **Act on Recommendation:**
                    *   **If 'walking' is recommended:** Inform the user of the walking distance and duration and that you're done.
                    *   **If 'driving' is recommended:** This is a multi-step process.
                        a.  Inform the user that driving is the best option and that you will now find the local fuel price to estimate the cost.
                        b.  Use the `perplexity_search` tool to find the current fuel price. Construct a very specific query, like: `What is the current price of 1 liter of petrol in {city from destination}?`.
                        c.  **CRITICAL:** You must parse the numerical price from the search result. Be diligent in finding this number. If you can't find it, ask the user for it.
                        d.  Once you have the fuel price, use the `calculate_driving_cost` tool. You will need the `distance_km` from the `get_travel_recommendation` tool's output and the `fuel_price_per_liter` you just found.
                        e.  You can also ask the user if they want a "safe/foreigner" estimate, which adds a 10% fuel markup and a flat fee. If they agree, set `apply_fuel_markup=True` and `additional_flat_fee` when calling `calculate_driving_cost`.
                
                4.  **Final Report:** Present a clear summary to the user, including the recommended mode, distance, duration, and a detailed cost breakdown if driving was chosen.
            """),
            add_datetime_to_instructions=True,
            show_tool_calls=True,
            markdown=True,
        )

    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        result = await self.agent.arun(message)
        yield result.content if hasattr(result, 'content') else str(result)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)

# Example Usage:
if __name__ == '__main__':
    # This is an example of how to run the agent asynchronously.
    # To make it work, you need to have OPENAI_API_KEY and PERPLEXITY_API_KEY in your .env file.
    
    from agno.models.openai import OpenAIChat
    
    async def main():
        """Asynchronous function to set up and run the agent."""
        # It's recommended to use a powerful model like gpt-4-turbo for better agent performance
        chat_model = OpenAIChat()
        maps_agent = GoogleMapsAgent(chat_model=chat_model)
        
        print("Running Google Maps Agent...")
        query = "I need to travel from the Eiffel Tower to the Louvre Museum in Paris. tell me cost for it with time and distance"
        
        print(f"\n--- User Query ---\n{query}")
        print("\n--- Agent Response ---")
        
        # The agent's run_async method returns an async generator.
        # We iterate over it to get the streaming response chunks.
        try:
            async for chunk in maps_agent.run_async(query):
                print(chunk, end="", flush=True)
        except Exception as e:
            print(f"\nAn error occurred during agent execution: {e}")
        
        print("\n\n--- Agent Run Finished ---")

    # This runs the main asynchronous function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent run interrupted by user.")