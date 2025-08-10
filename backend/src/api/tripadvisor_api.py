import os
import asyncio
import httpx
from dotenv import load_dotenv
load_dotenv('backend/.env')

class TripAdvisorAPIClient:
    """
    An asynchronous client for interacting with the TripAdvisor API on RapidAPI.
    """

    def __init__(self):
        """
        Initializes the TripAdvisorAPIClient.

        Loads the API key from the .env file and sets up the request headers.
        Raises:
            ValueError: If the TRIPADVISOR_API_KEY is not found in the environment variables.
        """
        load_dotenv()
        self.api_key = os.getenv("TRIPADVISOR_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please create a .env file and add TRIPADVISOR_API_KEY.")

        self.base_url = "https://tripadvisor16.p.rapidapi.com/api/v1"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
        }

    async def _make_request(self, method, endpoint, params=None):
        """
        Helper method to make asynchronous requests to the API.

        Args:
            method (str): HTTP method (e.g., 'GET').
            endpoint (str): API endpoint to call.
            params (dict, optional): Query parameters for the request. Defaults to None.

        Returns:
            dict: The JSON response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, params=params, timeout=30.0)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                return response.json()
            except httpx.HTTPStatusError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except httpx.RequestError as req_err:
                print(f"Request error occurred: {req_err}")
            except KeyError as key_err:
                print(f"Key error in JSON response: {key_err}")
            return None

    async def search_hotels_by_city(self, city_name, currency="USD"):
        """
        Searches for hotels in a given city asynchronously.

        Args:
            city_name (str): The name of the city to search for hotels in.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            list: A list of hotels found in the specified city.
        """
        # 1. Get location ID for the city
        location_data = await self._make_request("GET", "/hotels/searchLocation", params={"query": city_name})
        if not location_data or "data" not in location_data or not location_data["data"]:
            return []
        
        try:
            location_id = location_data["data"][0]["locationId"]
        except (KeyError, IndexError):
            print(f"Could not find locationId for city: {city_name}")
            return []

        # 2. Search for hotels using the location ID
        hotel_data = await self._make_request("GET", "/hotels/searchHotels", params={"locationId": location_id, "currency": currency})
        return hotel_data.get("data", {}).get("data", []) if hotel_data else []

    async def get_hotel_details(self, hotel_id, currency="USD"):
        """
        Retrieves details for a specific hotel asynchronously.

        Args:
            hotel_id (str): The ID of the hotel.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            dict: The details of the specified hotel.
        """
        return await self._make_request("GET", "/hotels/getHotelDetails", params={"id": hotel_id, "currency": currency})

    async def search_restaurants_by_city(self, city_name, currency="USD"):
        """
        Searches for restaurants in a given city asynchronously.

        Args:
            city_name (str): The name of the city to search for restaurants in.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            list: A list of restaurants found in the specified city.
        """
        # 1. Get location ID for the city
        location_data = await self._make_request("GET", "/restaurant/searchLocation", params={"query": city_name})
        if not location_data or "data" not in location_data or not location_data["data"]:
            return []
            
        try:
            location_id = location_data["data"][0]["locationId"]
        except (KeyError, IndexError):
            print(f"Could not find locationId for city: {city_name}")
            return []

        # 2. Search for restaurants using the location ID
        restaurant_data = await self._make_request("GET", "/restaurant/searchRestaurants", params={"locationId": location_id, "currency": currency})
        return restaurant_data.get("data", {}).get("data", []) if restaurant_data else []

    async def get_restaurant_details(self, restaurant_id, currency="USD"):
        """
        Retrieves details for a specific restaurant using the V2 endpoint asynchronously.

        Args:
            restaurant_id (str): The ID of the restaurant.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            dict: The details of the specified restaurant.
        """
        return await self._make_request("GET", "/restaurant/getRestaurantDetailsV2", params={"id": restaurant_id, "currency": currency})

    async def get_supported_currencies(self):
        """
        Retrieves a list of currencies supported by the API asynchronously.

        Returns:
            dict: A list of supported currencies.
        """
        return await self._make_request("GET", "/getCurrency")

async def main():
    """Main async function to run example usage."""
    try:
        # Initialize the client
        client = TripAdvisorAPIClient()

        # --- Example Usage ---

        # Search for hotels in New York
        print("--- Searching for Hotels in New York ---")
        hotels = await client.search_hotels_by_city("New York")
        if hotels:
            print(f"Found {len(hotels)} hotels.")
            # Get details for the first hotel
            first_hotel_id = hotels[0].get("id")
            if first_hotel_id:
                print(f"\n--- Getting Details for Hotel ID: {first_hotel_id} ---")
                hotel_details = await client.get_hotel_details(first_hotel_id)
                if hotel_details:
                    print(f"Hotel Name: {hotel_details.get('data', {}).get('name', 'N/A')}")
        print("-" * 30)

        # To avoid hitting rate limits on the free tier of RapidAPI
        print("Waiting for 30 seconds before next API call...")
        await asyncio.sleep(30)

        # Search for restaurants in Paris
        print("--- Searching for Restaurants in Paris ---")
        restaurants = await client.search_restaurants_by_city("Paris")
        if restaurants:
            print(f"Found {len(restaurants)} restaurants.")
            # Get details for the first restaurant
            first_restaurant_id = restaurants[0].get("id")
            if first_restaurant_id:
                print(f"\n--- Getting Details for Restaurant ID: {first_restaurant_id} ---")
                restaurant_details = await client.get_restaurant_details(first_restaurant_id)
                if restaurant_details:
                     print(f"Restaurant Name: {restaurant_details.get('data', {}).get('name', 'N/A')}")
        print("-" * 30)

    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
