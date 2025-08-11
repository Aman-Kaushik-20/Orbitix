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

# Perplexity API URL
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class GoogleMapsAgent:
    def __init__(self, google_maps_api_key: str, perplexity_api_key: str, openai_chat_model: OpenAIChat):
        """
        Initializes the GoogleMapsAgent.

        Args:
            google_maps_api_key (str): The API key for Google Maps.
            perplexity_api_key (str): The API key for Perplexity AI.
            chat_model (OpenAIChat): An instance of the OpenAI chat model.
        """
        if not google_maps_api_key:
            raise ValueError("Google Maps API key not provided.")
        if not perplexity_api_key:
            raise ValueError("Perplexity API key not provided.")
            
        self.gmaps_client = googlemaps.Client(key=google_maps_api_key)
        self.agent = self.setup_agent(
            perplexity_api_key=perplexity_api_key,
            chat_model=openai_chat_model
        )

    def setup_agent(self, perplexity_api_key: str, chat_model: OpenAIChat) -> Agent:
        """
        Sets up and configures the agent with its tools and instructions.

        Args:
            perplexity_api_key (str): The API key for Perplexity AI.
            chat_model (OpenAIChat): An instance of the OpenAI chat model.

        Returns:
            Agent: A fully configured instance of the agno.agent.Agent.
        """
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
                walking_matrix = self.gmaps_client.distance_matrix(source, destination, mode='walking')
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
                    driving_matrix = self.gmaps_client.distance_matrix(source, destination, mode='driving')
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
            if not perplexity_api_key:
                return {"error": "Perplexity API key not configured"}
            
            headers = {"Authorization": f"Bearer {perplexity_api_key}", "Content-Type": "application/json"}
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

        agent = Agent(
            name="Google Maps Travel Assistant",
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
        return agent

    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        result = await self.agent.arun(message)
        yield result.content if hasattr(result, 'content') else str(result)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)

# Example Usage:
# if __name__ == '__main__':
#     from agno.models.openai import OpenAIChat
    
#     async def main():
#         """Asynchronous function to set up and run the agent."""
#         gmaps_key = os.getenv("GOOGLE_MAPS_API_KEY")
#         perplexity_key = os.getenv("PERPLEXITY_API_KEY")

#         if not gmaps_key or not perplexity_key:
#             print("Error: GOOGLE_MAPS_API_KEY and PERPLEXITY_API_KEY must be set in your .env file.")
#             return

#         chat_model = OpenAIChat(id="gpt-4o")
#         maps_agent = GoogleMapsAgent(
#             google_maps_api_key=gmaps_key,
#             perplexity_api_key=perplexity_key,
#             chat_model=chat_model
#         )
        
#         print("Running Google Maps Agent...")
#         query = "I need to travel from the Eiffel Tower to the Louvre Museum in Paris. tell me cost for it with time and distance"
        
#         print(f"\n--- User Query ---\n{query}")
#         print("\n--- Agent Response ---")
        
#         try:
#             async for chunk in maps_agent.run_async(query):
#                 print(chunk, end="", flush=True)
#         except Exception as e:
#             print(f"\nAn error occurred during agent execution: {e}")
        
#         print("\n\n--- Agent Run Finished ---")

#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\nAgent run interrupted by user.")