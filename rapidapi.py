import os
import asyncio
import httpx
import re
from dotenv import load_dotenv
load_dotenv('backend/.env')

class TripAdvisorAPIClient:
    """
    An enhanced asynchronous client for interacting with the TripAdvisor API on RapidAPI.
    Handles responses correctly and extracts only important information.
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
            "x-rapidapi-key": self.api_key,
            "X-rapidapi-host": "tripadvisor16.p.rapidapi.com"
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
        """
        Extract geo ID from location data, handling different formats.
        
        Args:
            location_item (dict): Location item from API response
            
        Returns:
            str: Extracted geo ID or None
        """
        # Try documentId first
        doc_id = location_item.get("documentId")
        if doc_id:
            # Handle formats like 'loc;60763;g60763'
            if ';' in str(doc_id):
                parts = str(doc_id).split(';')
                for part in parts:
                    if part.isdigit():
                        return part
            elif str(doc_id).isdigit():
                return str(doc_id)
        
        # Try geoId as fallback
        geo_id = location_item.get("geoId")
        if geo_id:
            return str(geo_id)
            
        return None

    def _clean_image_url(self, url):
        """
        Clean image URL by removing template parameters.
        
        Args:
            url (str): Image URL with template parameters
            
        Returns:
            str: Clean image URL
        """
        if not url:
            return ""
        
        # Remove template parameters like ?w={width}&h={height}&s=1
        cleaned_url = re.sub(r'\?w=\{width\}&h=\{height\}&s=\d+', '', url)
        # Also handle other variations
        cleaned_url = re.sub(r'\?.*', '', cleaned_url)
        return cleaned_url

    def _get_actual_image_urls(self, photos_data):
        """
        Extract actual image URLs from photos data.
        
        Args:
            photos_data (list): List of photo objects
            
        Returns:
            list: List of clean image URLs
        """
        urls = []
        for photo in photos_data[:5]:  # Top 5 images
            # Handle different photo data structures
            if isinstance(photo, dict):
                # Try different possible paths for image URLs
                url = None
                if "sizes" in photo:
                    url = photo.get("sizes", {}).get("urlTemplate")
                elif "urlTemplate" in photo:
                    url = photo.get("urlTemplate")
                elif "__typename" in photo and "sizes" in photo:
                    url = photo.get("sizes", {}).get("urlTemplate")
                
                if url:
                    # Convert template to actual URL with reasonable dimensions
                    actual_url = url.replace("{width}", "400").replace("{height}", "300")
                    clean_url = self._clean_image_url(actual_url)
                    if clean_url:
                        urls.append(clean_url)
        
        return urls

    def _extract_hotel_summary(self, hotel_data):
        """Extract important information from hotel data"""
        # Clean hotel name (remove numbering)
        name = hotel_data.get("title", "")
        name = re.sub(r'^\d+\.\s*', '', name)  # Remove "1. " or "30. " etc.
        
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
        # Clean hero image URL
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
        """
        Separate function to get hotel data using geo ID.
        
        Args:
            geo_id (str): The geo ID for the location
            check_in (str): Check-in date
            check_out (str): Check-out date
            currency (str): Currency for pricing
            
        Returns:
            dict: Hotel search results
        """
        return await self._make_request("GET", "/hotels/searchHotels", 
                                      params={"geoId": geo_id, 
                                             "checkIn": check_in, 
                                             "checkOut": check_out, 
                                             "currency": currency})

    async def search_hotels_by_city(self, city_name, currency="USD", limit=5):
        """
        Searches for hotels in a given city asynchronously.

        Args:
            city_name (str): The name of the city to search for hotels in.
            currency (str, optional): The currency for pricing. Defaults to "USD".
            limit (int, optional): Maximum number of hotels to return. Defaults to 5.

        Returns:
            list: A list of top hotels with important information only.
        """
        # 1. Get location ID for the city
        location_data = await self._make_request("GET", "/hotels/searchLocation", params={"query": city_name})
        if not location_data or not location_data.get("status") or "data" not in location_data or not location_data["data"]:
            return []

        # Find the first suitable location (removed trackingItems check)
        geo_id = None
        for item in location_data["data"]:
            extracted_id = self._extract_geo_id(item)
            if extracted_id:
                geo_id = extracted_id
                break

        if not geo_id:
            print(f"Could not find geo ID for city: {city_name}")
            return []

        print(f"Using geo ID: {geo_id} for city: {city_name}")

        # 2. Search for hotels using the geo ID
        hotel_data = await self._get_hotel_data(geo_id, currency=currency)

        if not hotel_data or not hotel_data.get("status") or not hotel_data.get("data", {}).get("data"):
            return []

        # Extract and return top hotels with important info only
        hotels = hotel_data["data"]["data"][:limit]
        return [self._extract_hotel_summary(hotel) for hotel in hotels]

    async def get_hotel_details(self, hotel_id, currency="USD"):
        """
        Retrieves detailed information for a specific hotel asynchronously.

        Args:
            hotel_id (str): The ID of the hotel.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            dict: Important details of the specified hotel.
        """
        response = await self._make_request("GET", "/hotels/getHotelDetails", 
                                          params={"id": hotel_id, 
                                                 "checkIn": "2025-08-11", 
                                                 "checkOut": "2025-08-15", 
                                                 "currency": currency})
        
        if not response or not response.get("status") or "data" not in response:
            return None

        data = response["data"]
        
        # Extract important hotel details
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
                ][:10]  # Top 10 amenities
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
        """
        Searches for restaurants in a given city asynchronously.

        Args:
            city_name (str): The name of the city to search for restaurants in.
            currency (str, optional): The currency for pricing. Defaults to "USD".
            limit (int, optional): Maximum number of restaurants to return. Defaults to 5.

        Returns:
            list: A list of top restaurants with important information only.
        """
        # 1. Get location ID for the city
        location_data = await self._make_request("GET", "/restaurant/searchLocation", params={"query": city_name})
        if not location_data or not location_data.get("status") or "data" not in location_data or not location_data["data"]:
            return []

        # Find the first city in results
        location_id = None
        for item in location_data["data"]:
            if item.get("placeType") == "CITY":
                location_id = item.get("locationId")
                break

        if not location_id:
            print(f"Could not find location ID for city: {city_name}")
            return []

        # 2. Search for restaurants using the location ID
        restaurant_data = await self._make_request("GET", "/restaurant/searchRestaurants", 
                                                 params={"locationId": location_id, "currency": currency})

        if not restaurant_data or not restaurant_data.get("status") or not restaurant_data.get("data", {}).get("data"):
            return []

        # Extract and return top restaurants with important info only
        restaurants = restaurant_data["data"]["data"][:limit]
        return [self._extract_restaurant_summary(restaurant) for restaurant in restaurants]

    async def get_restaurant_details(self, restaurant_id, currency="USD"):
        """
        Retrieves detailed information for a specific restaurant asynchronously.

        Args:
            restaurant_id (str): The ID of the restaurant (restaurantsId format).
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            dict: Important details of the specified restaurant.
        """
        response = await self._make_request("GET", "/restaurant/getRestaurantDetailsV2", 
                                          params={"restaurantsId": restaurant_id, "currency": currency})
        
        if not response or not response.get("status") or "data" not in response:
            return None

        location_data = response["data"].get("location", {})
        overview_data = response["data"].get("overview", {})
        
        # Extract important restaurant details
        restaurant_details = {
            "name": location_data.get("name"),
            "rating": float(location_data.get("rating", 0)),
            "review_count": int(location_data.get("num_reviews", 0)),
            "ranking": location_data.get("ranking"),
            "price_level": location_data.get("price_level"),
            "price_range": location_data.get("price"),
            "description": location_data.get("description"),
            "address": location_data.get("address"),
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
            ][:10]  # Top 10 features
        
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
            # Convert minutes to time format
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
        """
        Get top hotels with their detailed information in one call.
        
        Args:
            city_name (str): City name to search
            currency (str): Currency for pricing
            limit (int): Number of hotels to return
            
        Returns:
            list: List of hotels with detailed information
        """
        # Get basic hotel info
        hotels = await self.search_hotels_by_city(city_name, currency, limit)
        
        detailed_hotels = []
        for hotel in hotels:
            if hotel.get('id'):
                # Get detailed info for each hotel
                details = await self.get_hotel_details(hotel['id'], currency)
                if details:
                    # Combine basic and detailed info
                    combined = {**hotel, **details}
                    detailed_hotels.append(combined)
                    
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
        
        return detailed_hotels

    async def get_supported_currencies(self):
        """
        Retrieves a list of currencies supported by the API asynchronously.

        Returns:
            dict: A list of supported currencies.
        """
        response = await self._make_request("GET", "/getCurrency")
        return response if response else {}

# Example usage function
async def example_usage():
    """Example function demonstrating the enhanced API client usage."""
    try:
        client = TripAdvisorAPIClient()

        # Get all hotels with detailed info for New York (top 5)
        print("=== TOP 5 HOTELS IN NEW YORK WITH DETAILS ===")
        detailed_hotels = await client.get_all_hotels_with_details("New York", limit=5)
        
        for i, hotel in enumerate(detailed_hotels, 1):
            print(f"{i}. {hotel['name']}")
            print(f"   Rating: {hotel['rating']} ({hotel['review_count']} reviews)")
            print(f"   Location: {hotel['location']}")
            print(f"   Address: {hotel.get('address', 'N/A')}")
            print(f"   Provider: {hotel['provider']}")
            print(f"   Price Info: {hotel.get('price_info', {})}")
            print(f"   Amenities: {', '.join(hotel.get('amenities', [])[:5])}")
            print(f"   Images: {len(hotel['images'])} URLs available")
            if hotel['images']:
                print(f"   Sample Image: {hotel['images'][0]}")
            print(f"   Nearby Restaurants: {len(hotel.get('nearby_restaurants', []))}")
            print(f"   Nearby Attractions: {len(hotel.get('nearby_attractions', []))}")
            print()

        # Wait to avoid rate limits
        await asyncio.sleep(2)

        # Search for restaurants in Mumbai (top 5)
        print("=== TOP 5 RESTAURANTS IN MUMBAI ===")
        restaurants = await client.search_restaurants_by_city("Mumbai", limit=5)
        for i, restaurant in enumerate(restaurants, 1):
            print(f"{i}. {restaurant['name']}")
            print(f"   Rating: {restaurant['rating']} ({restaurant['review_count']} reviews)")
            print(f"   Price: {restaurant['price_tag']}")
            print(f"   Cuisines: {', '.join(restaurant['cuisines'][:3])}")
            print(f"   Status: {restaurant['status']}")
            if restaurant['image']:
                print(f"   Image: {restaurant['image']}")
            print()

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

# Run the example
if __name__ == "__main__":
    asyncio.run(example_usage())