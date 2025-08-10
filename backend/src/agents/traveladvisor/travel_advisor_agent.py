import os
import asyncio
import httpx
import re
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool

load_dotenv('backend/.env')

class TripAdvisorAgent:
    """
    An enhanced asynchronous agentic client for interacting with the TripAdvisor API.
    Uses an AI agent to intelligently handle travel-related queries and recommendations.
    """

    def __init__(self, trip_advisor_api_key:str):
        """
        Initializes the TripAdvisorAgent with API credentials and AI agent.

        Raises:
            ValueError: If the TRIPADVISOR_API_KEY is not found in the environment variables.
        """
        load_dotenv()
        self.trip_advisor_api_key = trip_advisor_api_key
        if not self.trip_advisor_api_key:
            raise ValueError("API key not found. Please create a .env file and add TRIPADVISOR_API_KEY.")

        self.base_url = "https://tripadvisor16.p.rapidapi.com/api/v1"
        self.headers = {
            "x-rapidapi-key": self.trip_advisor_api_key,
            "X-rapidapi-host": "tripadvisor16.p.rapidapi.com"
        }

        # Tool definitions for the agent
        @tool(
            name="search_hotels",
            description="Search for hotels in a specific city with ratings, prices, and basic information"
        )
        async def _search_hotels_tool(city_name: str, currency: str = "USD", limit: int = 5):
            """Search for hotels in a city"""
            return await self.search_hotels_by_city(city_name, currency, limit)

        @tool(
            name="get_hotel_details",
            description="Get detailed information about a specific hotel including amenities, nearby attractions, and reviews"
        )
        async def _get_hotel_details_tool(hotel_id: str, currency: str = "USD"):
            """Get detailed hotel information"""
            return await self.get_hotel_details(hotel_id, currency)

        @tool(
            name="search_restaurants",
            description="Search for restaurants in a specific city with ratings, cuisines, and basic information"
        )
        async def _search_restaurants_tool(city_name: str, currency: str = "USD", limit: int = 5):
            """Search for restaurants in a city"""
            return await self.search_restaurants_by_city(city_name, currency, limit)

        @tool(
            name="get_restaurant_details",
            description="Get detailed information about a specific restaurant including menu, hours, and features"
        )
        async def _get_restaurant_details_tool(restaurant_id: str, currency: str = "USD"):
            """Get detailed restaurant information"""
            return await self.get_restaurant_details(restaurant_id, currency)

        @tool(
            name="get_comprehensive_city_guide",
            description="Get a complete travel guide for a city including top hotels and restaurants with full details"
        )
        async def _get_comprehensive_city_guide_tool(city_name: str, currency: str = "USD", hotel_limit: int = 3, restaurant_limit: int = 3):
            """Get comprehensive city travel guide"""
            # Get hotels with details
            hotels = await self.get_all_hotels_with_details(city_name, currency, hotel_limit)
            # Get restaurants
            restaurants = await self.get_all_restaurants_with_details(city_name, currency, restaurant_limit)
            
            return {
                "city": city_name,
                "hotels": hotels,
                "restaurants": restaurants,
                "total_hotels": len(hotels),
                "total_restaurants": len(restaurants)
            }

        @tool(
            name="get_supported_currencies",
            description="Get list of supported currencies for pricing"
        )
        async def _get_supported_currencies_tool():
            """Get supported currencies"""
            return await self.get_supported_currencies()
        

        # Initialize the AI agent with tools
        self.agent = Agent(
            name="Hotel And Restaurant Recommender",
            model=OpenAIChat(id="gpt-4o"),
            tools=[
                _search_hotels_tool,
                _get_hotel_details_tool,
                _search_restaurants_tool,
                _get_restaurant_details_tool,
                _get_comprehensive_city_guide_tool,
                _get_supported_currencies_tool
            ],
            description="You are a Travel Assistant AI that helps users find hotels, restaurants, and plan their trips using TripAdvisor data.",
            instructions=[
                "You are an intelligent travel assistant powered by TripAdvisor data.",
                "**Your Tools & Their Purposes:**",
                "1. **search_hotels:** Gets hotel summaries based on city name keyword search",
                "2. **get_hotel_details:** Gets detailed information for a specific hotel using hotel ID from search_hotels results",
                "3. **search_restaurants:** Gets restaurant summaries based on city name keyword search", 
                "4. **get_restaurant_details:** Gets detailed information for a specific restaurant using restaurant ID from search_restaurants results",
                "5. **get_comprehensive_city_guide:** Gets everything (hotels + restaurants with full details) from just a city name - this is an aggregated function",
                "6. **get_supported_currencies:** Gets available currency options for pricing",
                "",
                "**CRITICAL WORKFLOW - Follow This Order:**",
                "1. **First Priority:** ALWAYS try get_comprehensive_city_guide first when user asks for city information, hotels, restaurants, or travel planning",
                "2. **Fallback Strategy:** If get_comprehensive_city_guide fails or doesn't provide enough info, then use the step-by-step approach:",
                "   - Use search_hotels to get hotel summaries from city name",
                "   - Then use get_hotel_details with specific hotel IDs from the search results",
                "   - Use search_restaurants to get restaurant summaries from city name", 
                "   - Then use get_restaurant_details with specific restaurant IDs from the search results",
                "3. **Individual Queries:** For specific hotel/restaurant details, use the direct detail tools with IDs",
                "",
                "**Tool Usage Rules:**",
                "- search_hotels: Input = city name → Output = hotel summaries with IDs",
                "- get_hotel_details: Input = hotel ID from search_hotels → Output = full hotel details",
                "- search_restaurants: Input = city name → Output = restaurant summaries with IDs",
                "- get_restaurant_details: Input = restaurant ID from search_restaurants → Output = full restaurant details",
                "- get_comprehensive_city_guide: Input = city name → Output = complete travel guide",
                "",
                "**Response Strategy:**",
                "- Always start with get_comprehensive_city_guide for city-based queries",
                "- If comprehensive guide works, present all information in organized format",
                "- If comprehensive guide fails, explain you'll gather info step-by-step and use individual tools",
                "- Include practical details: ratings, prices, addresses, amenities, cuisines",
                "- For Images return the EXact URLS along with other details...."
                "- Be conversational and helpful in your presentation"
                ],
            markdown=True,
            show_tool_calls=True,
        )

    async def ask(self, query: str):
        """
        Process a natural language travel query using the AI agent.
        
        Args:
            query (str): Natural language query about travel, hotels, restaurants, etc.
            
        Returns:
            str: AI agent's response with relevant travel information
        """
        try:
            result = await self.agent.arun(query)
            return result.content if hasattr(result, "content") else str(result)
        except Exception as e:
            return f"Sorry, I encountered an error while processing your request: {e}"

    # Original API methods (unchanged from your code)
    async def _make_request(self, method, endpoint, params=None):
        """Helper method to make asynchronous requests to the API."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, params=params, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except httpx.RequestError as req_err:
                print(f"Request error occurred: {req_err}")
            except Exception as e:
                print(f"Unexpected error: {e}")
            return None

    def _extract_geo_id(self, location_item):
        """Extract geo ID from location data, handling different formats."""
        doc_id = location_item.get("documentId")
        if doc_id:
            if ';' in str(doc_id):
                parts = str(doc_id).split(';')
                for part in parts:
                    if part.isdigit():
                        return part
            elif str(doc_id).isdigit():
                return str(doc_id)
        
        geo_id = location_item.get("geoId")
        if geo_id:
            return str(geo_id)
            
        return None

    def _clean_image_url(self, url):
        """Clean image URL by removing template parameters."""
        if not url:
            return ""
        
        cleaned_url = re.sub(r'\?w=\{width\}&h=\{height\}&s=\d+', '', url)
        cleaned_url = re.sub(r'\?.*', '', cleaned_url)
        return cleaned_url

    def _get_actual_image_urls(self, photos_data):
        """Extract actual image URLs from photos data."""
        urls = []
        for photo in photos_data[:5]:
            if isinstance(photo, dict):
                url = None
                if "sizes" in photo:
                    url = photo.get("sizes", {}).get("urlTemplate")
                elif "urlTemplate" in photo:
                    url = photo.get("urlTemplate")
                elif "__typename" in photo and "sizes" in photo:
                    url = photo.get("sizes", {}).get("urlTemplate")
                
                if url:
                    actual_url = url.replace("{width}", "400").replace("{height}", "300")
                    clean_url = self._clean_image_url(actual_url)
                    if clean_url:
                        urls.append(clean_url)
        
        return urls

    def _extract_hotel_summary(self, hotel_data):
        """Extract important information from hotel data"""
        name = hotel_data.get("title", "")
        name = re.sub(r'^\d+\.\s*', '', name)
        
        return {
            "id": hotel_data.get("id"),
            "name": name,
            "primary_info": hotel_data.get("primaryInfo"),
            "location": hotel_data.get("secondaryInfo"),
            "rating": hotel_data.get("bubbleRating", {}).get("rating"),
            "review_count": hotel_data.get("bubbleRating", {}).get("count"),
            "provider": hotel_data.get("provider"),
            "badge": hotel_data.get("badge", {}).get("type"),
            "price_display": hotel_data.get("priceForDisplay"),
            "strike_price": hotel_data.get("strikethroughPrice"),
            "price_details": hotel_data.get("priceDetails"),
            "images": self._get_actual_image_urls(hotel_data.get("cardPhotos", []))
        }

    def _extract_restaurant_summary(self, restaurant_data):
        """Extract important information from restaurant data"""
        hero_img = restaurant_data.get("heroImgUrl", "")
        clean_hero_img = self._clean_image_url(hero_img) if hero_img else None
        
        return {
            "id": restaurant_data.get("locationId"),
            "restaurant_id": restaurant_data.get("restaurantsId"),
            "name": restaurant_data.get("name"),
            "rating": restaurant_data.get("averageRating"),
            "review_count": restaurant_data.get("userReviewCount"),
            "price_tag": restaurant_data.get("priceTag"),
            "status": restaurant_data.get("currentOpenStatusText"),
            "cuisines": restaurant_data.get("establishmentTypeAndCuisineTags", []),
            "has_menu": restaurant_data.get("hasMenu"),
            "menu_url": restaurant_data.get("menuUrl"),
            "has_delivery": restaurant_data.get("offers", {}).get("hasDelivery"),
            "has_reservation": restaurant_data.get("offers", {}).get("hasReservation"),
            "image": clean_hero_img
        }

    async def _get_hotel_data(self, geo_id, check_in="2025-08-11", check_out="2025-08-15", currency="USD"):
        """Separate function to get hotel data using geo ID."""
        return await self._make_request("GET", "/hotels/searchHotels", 
                                      params={"geoId": geo_id, 
                                             "checkIn": check_in, 
                                             "checkOut": check_out, 
                                             "currency": currency})

    async def search_hotels_by_city(self, city_name, currency="USD", limit=5):
        """Searches for hotels in a given city asynchronously."""
        location_data = await self._make_request("GET", "/hotels/searchLocation", params={"query": city_name})
        if not location_data or not location_data.get("status") or "data" not in location_data or not location_data["data"]:
            return []

        geo_id = None
        for item in location_data["data"]:
            extracted_id = self._extract_geo_id(item)
            if extracted_id:
                geo_id = extracted_id
                break

        if not geo_id:
            print(f"Could not find geo ID for city: {city_name}")
            return []

        hotel_data = await self._get_hotel_data(geo_id, currency=currency)

        if not hotel_data or not hotel_data.get("status") or not hotel_data.get("data", {}).get("data"):
            return []

        hotels = hotel_data["data"]["data"][:limit]
        return [self._extract_hotel_summary(hotel) for hotel in hotels]

    async def get_hotel_details(self, hotel_id, currency="USD"):
        """Retrieves detailed information for a specific hotel asynchronously."""
        response = await self._make_request("GET", "/hotels/getHotelDetails", 
                                          params={"id": hotel_id, 
                                                 "checkIn": "2025-08-11", 
                                                 "checkOut": "2025-08-15", 
                                                 "currency": currency})
        
        if not response or not response.get("status") or "data" not in response:
            return None

        data = response["data"]
        
        hotel_details = {
            "name": data.get("title"),
            "rating": data.get("rating"),
            "review_count": data.get("numberReviews"),
            "ranking": data.get("rankingDetails"),
            "description": data.get("about", {}).get("title"),
            "address": data.get("location", {}).get("address"),
            "neighborhood": data.get("location", {}).get("neighborhood", {}).get("name"),
            "distance_to_airport": None,
            "amenities": [],
            "languages": [],
            "tags": data.get("about", {}).get("tags", []),
            "images": self._get_actual_image_urls(data.get("photos", [])),
            "nearby_restaurants": [],
            "nearby_attractions": [],
            "sample_reviews": [],
            "price_info": self._extract_price_info(data.get("price", {}))
        }

        # Extract amenities and languages
        about_content = data.get("about", {}).get("content", [])
        for section in about_content:
            if section.get("title") == "Amenities":
                hotel_details["amenities"] = [
                    item.get("title") for item in section.get("content", [])
                    if item.get("title")
                ][:10]
            elif section.get("title") == "Available languages":
                for item in section.get("content", []):
                    if item.get("content"):
                        hotel_details["languages"] = item["content"].split(", ")

        # Extract distance to airport
        getting_there = data.get("location", {}).get("gettingThere", {}).get("content", [])
        for item in getting_there:
            if "Airport" in item:
                hotel_details["distance_to_airport"] = item

        # Extract nearby restaurants (top 5)
        restaurants = data.get("restaurantsNearby", {}).get("content", [])[:5]
        for restaurant in restaurants:
            hotel_details["nearby_restaurants"].append({
                "name": restaurant.get("title"),
                "rating": restaurant.get("bubbleRating", {}).get("rating"),
                "cuisine": restaurant.get("primaryInfo"),
                "distance": restaurant.get("distance")
            })

        # Extract nearby attractions (top 5)
        attractions = data.get("attractionsNearby", {}).get("content", [])[:5]
        for attraction in attractions:
            hotel_details["nearby_attractions"].append({
                "name": attraction.get("title"),
                "rating": attraction.get("bubbleRating", {}).get("rating"),
                "type": attraction.get("primaryInfo"),
                "distance": attraction.get("distance")
            })

        # Extract sample reviews (top 2)
        reviews = data.get("reviews", {}).get("content", [])[:2]
        for review in reviews:
            hotel_details["sample_reviews"].append({
                "title": review.get("title"),
                "text": review.get("text", "")[:200] + "..." if len(review.get("text", "")) > 200 else review.get("text", ""),
                "rating_text": review.get("bubbleRatingText"),
                "date": review.get("publishedDate")
            })

        return hotel_details

    def _extract_price_info(self, price_data):
        """Extract pricing information from price data"""
        if not price_data:
            return {"status": "No pricing available"}
        
        return {
            "display_price": price_data.get("displayPrice"),
            "strike_price": price_data.get("strikeThroughPrice"),
            "status": price_data.get("status"),
            "provider": price_data.get("providerName"),
            "free_cancellation": price_data.get("freeCancellation"),
            "pricing_period": price_data.get("pricingPeriod")
        }

    async def search_restaurants_by_city(self, city_name, currency="USD", limit=5):
        """Searches for restaurants in a given city asynchronously."""
        location_data = await self._make_request("GET", "/restaurant/searchLocation", params={"query": city_name})
        if not location_data or not location_data.get("status") or "data" not in location_data or not location_data["data"]:
            return []

        location_id = None
        # Loosen the check to accept other location types if "CITY" is not found
        for item in location_data["data"]:
            if item.get("locationId"):
                location_id = item.get("locationId")
                break

        if not location_id:
            print(f"Could not find location ID for city: {city_name}")
            return []

        restaurant_data = await self._make_request("GET", "/restaurant/searchRestaurants", 
                                                 params={"locationId": location_id, "currency": currency})

        if not restaurant_data or not restaurant_data.get("status") or not restaurant_data.get("data", {}).get("data"):
            return []

        restaurants = restaurant_data["data"]["data"][:limit]
        return [self._extract_restaurant_summary(restaurant) for restaurant in restaurants]

    async def get_restaurant_details(self, restaurant_id, currency="USD"):
        """Retrieves detailed information for a specific restaurant asynchronously."""
        response = await self._make_request("GET", "/restaurant/getRestaurantDetailsV2", 
                                          params={"restaurantsId": restaurant_id, "currency": currency})
        
        if not response or not response.get("status") or "data" not in response:
            return None

        location_data = response["data"].get("location", {})
        overview_data = response["data"].get("overview", {})
        
        restaurant_details = {
            "name": location_data.get("name"),
            "rating": float(location_data.get("rating", 0)),
            "review_count": int(location_data.get("num_reviews", 0)),
            "ranking": location_data.get("ranking"),
            "price_level": location_data.get("price_level"),
            "price_range": location_data.get("price"),
            "description": location_data.get("description"),
            "address": location_data.get("address", {}).get("address"),
            "neighborhood": location_data.get("neighborhood_info", [{}])[0].get("name") if location_data.get("neighborhood_info") else None,
            "website": location_data.get("website"),
            "email": location_data.get("email"),
            "is_open": not location_data.get("is_closed", True),
            "open_status": location_data.get("open_now_text"),
            "cuisines": [cuisine.get("name") for cuisine in location_data.get("cuisine", [])],
            "dietary_options": [diet.get("name") for diet in location_data.get("dietary_restrictions", [])],
            "hours": self._extract_hours(location_data.get("hours", {})),
            "features": [],
            "meals_served": [],
            "image_url": self._clean_image_url(location_data.get("photo", {}).get("images", {}).get("large", {}).get("url", ""))
        }

        # Extract features and meals from detail card
        detail_card = overview_data.get("detailCard", {}).get("tagTexts", {})
        
        if "features" in detail_card:
            restaurant_details["features"] = [
                tag.get("tagValue") for tag in detail_card["features"].get("tags", [])
            ][:10]
        
        if "meals" in detail_card:
            restaurant_details["meals_served"] = [
                tag.get("tagValue") for tag in detail_card["meals"].get("tags", [])
            ]

        return restaurant_details

    def _extract_hours(self, hours_data):
        """Extract operating hours information"""
        if not hours_data or not hours_data.get("week_ranges"):
            return "Hours not available"
        
        try:
            def minutes_to_time(minutes):
                hours = minutes // 60
                mins = minutes % 60
                period = "AM" if hours < 12 else "PM"
                display_hour = hours if hours <= 12 else hours - 12
                if display_hour == 0:
                    display_hour = 12
                return f"{display_hour}:{mins:02d} {period}"
            
            week_ranges = hours_data["week_ranges"]
            if week_ranges and week_ranges[0]:
                first_range = week_ranges[0][0]
                open_time = minutes_to_time(first_range["open_time"])
                close_time = minutes_to_time(first_range["close_time"])
                return f"{open_time} - {close_time}"
        except (KeyError, IndexError, TypeError):
            pass
        
        return "Hours not available"

    async def get_all_hotels_with_details(self, city_name, currency="USD", limit=5):
        """Get top hotels with their detailed information in one call."""
        hotels = await self.search_hotels_by_city(city_name, currency, limit)
        
        detailed_hotels = []
        for hotel in hotels:
            if hotel.get('id'):
                details = await self.get_hotel_details(hotel['id'], currency)
                if details:
                    combined = {**hotel, **details}
                    detailed_hotels.append(combined)
                    
                await asyncio.sleep(0.5)
        
        return detailed_hotels




    async def get_all_restaurants_with_details(self, city_name, currency="USD", limit=5):
        """Get top restaurants with their detailed information in one call."""
        restaurants = await self.search_restaurants_by_city(city_name, currency, limit)
        
        detailed_restaurants = []
        for restaurant in restaurants:
            if restaurant.get('restaurant_id'):
                details = await self.get_restaurant_details(restaurant['restaurant_id'], currency)
                if details:
                    combined = {**restaurant, **details}
                    detailed_restaurants.append(combined)
                    
                await asyncio.sleep(0.5)
        
        return detailed_restaurants





# Run the example
if __name__ == "__main__":
    # Example usage function
    async def example_usage():
        """Example function demonstrating the agentic TripAdvisor client usage."""
        try:
            # Initialize the agent
            trip_agent = TripAdvisorAgent()

            # Example queries using natural language
            queries = [
                "Find me the best hotels in Mumbai",
                # "I'm looking for great restaurants in Paris. Show me top rated ones with their details",
                # "Plan a complete travel guide for New York with hotels and restaurants",
                # "What are some luxury hotels in Dubai with spa facilities?",
                # "Find budget-friendly restaurants in Bangkok with good local cuisine"
            ]

            for query in queries:
                print(f"\n{'='*50}")
                print(f"QUERY: {query}")
                print(f"{'='*50}")
                
                response = await trip_agent.ask(query)
                print(response)
                
                # Wait between queries to avoid rate limits
                await asyncio.sleep(2)

        except ValueError as e:
            print(f"Configuration Error: {e}")
        except Exception as e:
            print(f"Unexpected Error: {e}")

    asyncio.run(example_usage())