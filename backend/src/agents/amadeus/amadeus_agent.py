#!/usr/bin/env python3
"""
AmadeusAgent - Unified class for Amadeus API operations
Combines airport search, flight search, and utility functions into a single agent.
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, AsyncGenerator
from textwrap import dedent

from amadeus import Client, ResponseError
from agno.agent import Agent
from agno.tools import tool
from agno.tools.reasoning import ReasoningTools
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
import os
from dotenv import load_dotenv
load_dotenv()


class AmadeusAgent:
    """Unified agent for Amadeus API operations including airport search, flight search, and utilities."""
    
    def __init__(self, amadeus_client:Client, openai_chat_model: OpenAIChat, anthropic_chat_model: Claude):
        self.amadeus_client = amadeus_client
        self.cached_airports = {}
        
        # Use pre-initialized model if provided, otherwise create new one
        model = openai_chat_model
        
        self.agent = self._setup_agent(model)
    
    def search_airports(self, keyword, max_results=20):
        """
        Search for airports based on a keyword (city name, airport name, or IATA code).
        
        Args:
            keyword (str): Search keyword (e.g., 'PAR', 'Paris', 'London')
            max_results (int): Maximum number of results to return (default: 20)
        
        Returns:
            list: List of airport dictionaries with name, iataCode, and cityName
        """
        try:
            amadeus = self.amadeus_client
            
            response = amadeus.reference_data.locations.get(
                keyword=keyword,
                subType=Location.ANY,
                page={'limit': max_results}
            )
            
            airports = []
            for location in response.data:
                if location.get('subType') in ['AIRPORT', 'CITY']:
                    airport_info = {
                        'name': location.get('name', ''),
                        'iataCode': location.get('iataCode', ''),
                        'cityName': location.get('address', {}).get('cityName', ''),
                        'countryName': location.get('address', {}).get('countryName', ''),
                        'subType': location.get('subType', '')
                    }
                    airports.append(airport_info)
            
            return airports
            
        except ResponseError as error:
            print(f"Amadeus API Error: {error}")
            return []
        except Exception as e:
            print(f"Error searching airports: {e}")
            return []
    
    def get_airport_details(self, iata_code):
        """
        Get detailed information about a specific airport using its IATA code.
        
        Args:
            iata_code (str): 3-letter IATA airport code (e.g., 'CDG')
        
        Returns:
            dict: Detailed airport information or None if not found
        """
        try:
            amadeus = self.amadeus_client
            
            response = amadeus.reference_data.locations.get(
                keyword=iata_code,
                subType=Location.AIRPORT
            )
            
            if response.data:
                location = response.data[0]
                return {
                    'name': location.get('name', ''),
                    'iataCode': location.get('iataCode', ''),
                    'cityName': location.get('address', {}).get('cityName', ''),
                    'countryName': location.get('address', {}).get('countryName', ''),
                    'timeZone': location.get('timeZoneOffset', ''),
                    'geoCode': location.get('geoCode', {}),
                    'subType': location.get('subType', '')
                }
            
            return None
            
        except ResponseError as error:
            print(f"Amadeus API Error: {error}")
            return None
        except Exception as e:
            print(f"Error getting airport details: {e}")
            return None
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, 
                      max_results=50, find_cheapest=False, date_range_days=7, quick_search=False):
        """
        Search for available flights based on given parameters.
        
        Args:
            origin (str): Origin airport IATA code (e.g., 'PAR')
            destination (str): Destination airport IATA code (e.g., 'NYC')
            departure_date (str): Departure date in YYYY-MM-DD format
            return_date (str, optional): Return date in YYYY-MM-DD format for round trip
            adults (int): Number of adult passengers (default: 1)
            max_results (int): Maximum number of flight offers to return (default: 50)
            find_cheapest (bool): Search across multiple dates for cheapest flights
            date_range_days (int): Days to search when find_cheapest=True (default: 7)
            quick_search (bool): Quick search with minimal results (default: False)
        
        Returns:
            dict: Dictionary containing flight offers and trip information
        """
        if departure_date == "tomorrow":
            tomorrow = datetime.now() + timedelta(days=1)
            departure_date = tomorrow.strftime('%Y-%m-%d')
        
        if quick_search:
            max_results = 3
            print(f"✈️  Quick search: {origin} → {destination} on {departure_date}")
        
        if find_cheapest:
            return self._find_cheapest_across_dates(origin, destination, departure_date, date_range_days, adults)
        
        return self._search_single_date(origin, destination, departure_date, return_date, adults, max_results, quick_search)
    
    def get_airport_info_batch(self, airport_codes):
        """Get information for multiple airports at once."""
        airports_info = {}
        
        for code in airport_codes:
            if code in self.cached_airports:
                airports_info[code] = self.cached_airports[code]
            else:
                try:
                    info = self.get_airport_details(code)
                    if info:
                        airports_info[code] = info
                        self.cached_airports[code] = info
                    else:
                        airports_info[code] = {'error': 'Airport not found'}
                except Exception as e:
                    airports_info[code] = {'error': str(e)}
        
        return airports_info
    
    def suggest_alternative_airports(self, city_keyword):
        """Suggest alternative airports for a city."""
        print(f"🔍 Finding alternative airports for: {city_keyword}")
        
        airports = self.search_airports(city_keyword, max_results=10)
        
        if not airports:
            print("❌ No airports found")
            return []
        
        alternatives = []
        for airport in airports:
            alternatives.append({
                'name': airport['name'],
                'iata_code': airport['iataCode'],
                'city': airport['cityName'],
                'country': airport['countryName'],
                'type': airport['subType']
            })
        
        print(f"✅ Found {len(alternatives)} alternatives:")
        for i, alt in enumerate(alternatives, 1):
            print(f"  {i}. {alt['name']} ({alt['iata_code']}) - {alt['type']}")
        
        return alternatives
    
    def _setup_agent(self, model):
        """Set up the Agent with tools."""
        @tool(
            name="search_airports",
            description="""Search for airports based on a keyword (city name, airport name, or IATA code).
        
        Args:
            keyword (str): Search keyword (e.g., 'PAR', 'Paris', 'London')
            max_results (int): Maximum number of results to return (default: 20)
        
        Returns:
            dict: Status and list of airport dictionaries with name, iataCode, cityName, countryName, and subType
        """,
            show_result=True
        )
        def search_airports_tool(keyword: str, max_results: int = 20):
            """Tool wrapper for search_airports."""
            airports = self.search_airports(keyword, max_results)
            return {
                "status": "success" if airports else "error",
                "airports": airports,
                "total_results": len(airports),
                "search_keyword": keyword,
                "message": "No airports found" if not airports else f"Found {len(airports)} airports"
            }
    
        @tool(
            name="get_airport_details", 
            description="""Get detailed information about a specific airport using its IATA code.
        
        Args:
            iata_code (str): 3-letter IATA airport code (e.g., 'CDG', 'JFK')
        
        Returns:
            dict: Status and detailed airport information including name, location, timezone, and coordinates
        """,
            show_result=True
        )
        def get_airport_details_tool(iata_code: str):
            """Tool wrapper for get_airport_details."""
            airport = self.get_airport_details(iata_code)
            if airport:
                return {
                    "status": "success",
                    "airport": airport
                }
            else:
                return {
                    "status": "error",
                    "message": f"Airport with IATA code '{iata_code}' not found",
                    "airport": None
                }
    
        @tool(
            name="search_flights",
            description="""Search for available flights with multiple search options.
        
        Args:
            origin (str): Origin airport IATA code (e.g., 'PAR', 'NYC')
            destination (str): Destination airport IATA code (e.g., 'NYC', 'LON')
            departure_date (str): Departure date in YYYY-MM-DD format or 'tomorrow'
            return_date (str, optional): Return date for round trip
            adults (int): Number of adult passengers (default: 1)
            max_results (int): Maximum results to return (default: 50)
            find_cheapest (bool): Search across multiple dates for cheapest flights
            date_range_days (int): Days to search when find_cheapest=True (default: 7)
            quick_search (bool): Quick search with top 3 results only
        
        Returns:
            dict: Flight search results with offers, pricing, and trip information
        """,
            show_result=True
        )
        def search_flights_tool(
            origin: str, 
            destination: str, 
            departure_date: str,
            return_date: Optional[str] = None,
            adults: int = 1,
            max_results: int = 50,
            find_cheapest: bool = False,
            date_range_days: int = 7,
            quick_search: bool = False
        ):
            """Tool wrapper for search_flights."""
            try:
                result = self.search_flights(
                    origin, destination, departure_date, return_date, adults, 
                    max_results, find_cheapest, date_range_days, quick_search
                )
                if 'error' not in result:
                    result['status'] = 'success'
                return result
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Flight search failed: {str(e)}",
                    "flights": []
                }
    
        @tool(
            name="get_airport_info_batch",
            description="""Get information for multiple airports at once with caching.
        
        Args:
            airport_codes (List[str]): List of IATA airport codes to look up
        
        Returns:
            dict: Dictionary mapping airport codes to their detailed information
        """,
            show_result=True
        )
        def get_airport_info_batch_tool(airport_codes: List[str]):
            """Tool wrapper for get_airport_info_batch."""
            airports_info = self.get_airport_info_batch(airport_codes)
            return {
                "status": "success",
                "airports": airports_info,
                "total_requested": len(airport_codes),
                "total_found": len([info for info in airports_info.values() if 'error' not in info])
            }
    
        @tool(
            name="suggest_alternative_airports",
            description="""Suggest alternative airports for a city or region.
        
        Args:
            city_keyword (str): City name or region to search for alternative airports
            max_results (int): Maximum number of alternatives to return (default: 10)
        
        Returns:
            dict: List of alternative airports with detailed information
        """, 
            show_result=True
        )
        def suggest_alternative_airports_tool(city_keyword: str, max_results: int = 10):
            """Tool wrapper for suggest_alternative_airports."""
            alternatives = self.suggest_alternative_airports(city_keyword)
            return {
                "status": "success" if alternatives else "error",
                "alternatives": alternatives,
                "search_keyword": city_keyword,
                "total_found": len(alternatives),
                "message": "No airports found" if not alternatives else f"Found {len(alternatives)} alternatives"
            }

        return Agent(
            name="Amadeus Travel Intelligence Agent",
            role="Flight Search and Airport Information Specialist",
            model=model,
            tools=[
                ReasoningTools(add_instructions=True),
                search_airports_tool,
                get_airport_details_tool, 
                search_flights_tool,
                get_airport_info_batch_tool,
                suggest_alternative_airports_tool
            ],
            instructions=dedent("""\
                You are an expert travel intelligence agent specialized in flight search and airport information! ✈️🌍

                Your capabilities:
                - Comprehensive airport search and information retrieval
                - Advanced flight search with multiple options (regular, cheapest, quick search)
                - Multi-route comparison and analysis
                - Alternative airport suggestions for flexible travel planning
                - Batch airport information processing

                SYSTEMATIC FLIGHT SEARCH APPROACH:
                For any flight search request, follow this exact workflow:
                
                1. **Airport Code Discovery**: First use search_airports_tool to find exact airport codes for:
                   - Departure location (based on user's origin city/airport keyword)
                   - Destination location (based on user's destination city/airport keyword)
                   
                2. **Airport Information Gathering**: Use get_airport_details_tool to get detailed information for:
                   - Selected departure airport (name, city, timezone, etc.)
                   - Selected destination airport (name, city, timezone, etc.)
                   
                3. **Flight Search Execution**: Finally use search_flights_tool with the discovered airport codes to:
                   - Search for available flights between the airports
                   - Apply appropriate search options (regular, cheapest, quick search)
                   - Present comprehensive flight results with all relevant details

                Flight Search Strategy Selection:
                - Regular search: Standard flight search with full details
                - Cheapest search (find_cheapest=True): Search across multiple dates to find best prices
                - Quick search (quick_search=True): Fast results with top 3 options only
                - Route comparison: Compare multiple origin/destination combinations

                Additional Tools Usage:
                - Use suggest_alternative_airports_tool when original search yields limited results
                - Use get_airport_info_batch_tool for efficient multi-airport information lookup
                - Always provide airport context (full names, cities) alongside IATA codes

                IMPORTANT: Never assume airport codes - always discover them first using search_airports_tool, 
                even for well-known cities like "Paris" or "New York" to ensure accuracy and provide 
                users with airport options.

                Always provide clear, actionable travel information with proper context including:
                - Airport names and locations
                - Flight details (prices, durations, airlines, segments)
                - Alternative options when applicable
            """),
            show_tool_calls=True,
            markdown=True,
        )
    
    async def run_async(self, message: str) -> AsyncGenerator[str, None]:
        """Run the agent asynchronously with streaming"""
        return await self.agent.arun(message)
    
    def run_sync(self, message: str) -> str:
        """Run the agent synchronously"""
        return self.agent.run(message)
    
    # Rest of the implementation methods remain the same...
    def _search_single_date(self, origin, destination, departure_date, return_date, adults, max_results, quick_search):
        """Search flights for a single date."""
        try:
            amadeus = self.amadeus_client
            
            search_params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "max": max_results
            }
            
            if return_date:
                search_params["returnDate"] = return_date
            
            flight_response = amadeus.shopping.flight_offers_search.get(**search_params)
            
            processed_flights = []
            for flight_offer in flight_response.data:
                processed_flight = self._process_flight_offer(flight_offer)
                processed_flights.append(processed_flight)
            
            result = {
                'flights': processed_flights,
                'search_params': {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date,
                    'return_date': return_date,
                    'adults': adults
                },
                'total_results': len(processed_flights)
            }
            
            if quick_search and processed_flights:
                print(f"Found {len(processed_flights)} flights:")
                for i, flight in enumerate(processed_flights, 1):
                    segments = flight['itineraries'][0]['segments']
                    print(f"  {i}. {flight['price']['total']} {flight['price']['currency']} - "
                          f"{segments[0]['departure']['time']} to {segments[-1]['arrival']['time']} "
                          f"({flight['itineraries'][0]['duration']})")
            
            return result
            
        except ResponseError as error:
            print(f"Amadeus API Error: {error}")
            return {'error': str(error), 'flights': []}
        except Exception as e:
            print(f"Error searching flights: {e}")
            return {'error': str(e), 'flights': []}
    
    def _find_cheapest_across_dates(self, origin, destination, departure_date, date_range_days, adults):
        """Find cheapest flights across multiple dates."""
        if not departure_date:
            tomorrow = datetime.now() + timedelta(days=1)
            departure_date = tomorrow.strftime('%Y-%m-%d')
        
        print(f"🔍 Searching for cheapest flights {origin} → {destination}")
        print(f"Date range: {departure_date} to {date_range_days} days ahead...")
        
        best_flights = []
        base_date = datetime.strptime(departure_date, '%Y-%m-%d')
        
        for day_offset in range(date_range_days):
            search_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            print(f"  Checking {search_date}...")
            
            try:
                results = self._search_single_date(origin, destination, search_date, None, adults, 3, False)
                
                if 'error' not in results and results['flights']:
                    flight = results['flights'][0]
                    flight_info = self._extract_flight_summary(flight, search_date)
                    best_flights.append(flight_info)
                        
            except Exception as e:
                print(f"    Error for {search_date}: {e}")
        
        best_flights.sort(key=lambda x: x['price'])
        
        return {
            'search_params': {
                'origin': origin,
                'destination': destination,
                'date_range': f"{departure_date} to {date_range_days} days",
                'total_dates_checked': len(best_flights)
            },
            'cheapest_flights': best_flights[:5],
            'price_range': {
                'min': min(best_flights, key=lambda x: x['price'])['price'] if best_flights else 0,
                'max': max(best_flights, key=lambda x: x['price'])['price'] if best_flights else 0
            }
        }
    
    def _extract_flight_summary(self, flight, search_date):
        """Extract summary information from a flight offer."""
        return {
            'date': search_date,
            'price': float(flight['price']['total']),
            'currency': flight['price']['currency'],
            'duration': flight['itineraries'][0]['duration'],
            'flight_id': flight['id'],
            'segments': len(flight['itineraries'][0]['segments']),
            'airline': flight['itineraries'][0]['segments'][0]['carrierCode']
        }
    
    def _process_flight_offer(self, flight_offer):
        """
        Process a single flight offer into a readable format.
        
        Args:
            flight_offer (dict): Raw flight offer data from Amadeus API
        
        Returns:
            dict: Processed flight offer with readable information
        """
        processed_offer = {
            'id': flight_offer.get('id', ''),
            'price': {
                'total': flight_offer.get('price', {}).get('total', ''),
                'currency': flight_offer.get('price', {}).get('currency', '')
            },
            'itineraries': []
        }
        
        for idx, itinerary in enumerate(flight_offer.get('itineraries', [])):
            itinerary_data = {
                'type': 'outbound' if idx == 0 else 'return',
                'duration': self._format_duration(itinerary.get('duration', '')),
                'segments': []
            }
            
            for segment in itinerary.get('segments', []):
                segment_data = {
                    'departure': {
                        'iataCode': segment.get('departure', {}).get('iataCode', ''),
                        'terminal': segment.get('departure', {}).get('terminal', ''),
                        'at': segment.get('departure', {}).get('at', ''),
                        'time': self._get_time_from_datetime(segment.get('departure', {}).get('at', ''))
                    },
                    'arrival': {
                        'iataCode': segment.get('arrival', {}).get('iataCode', ''),
                        'terminal': segment.get('arrival', {}).get('terminal', ''),
                        'at': segment.get('arrival', {}).get('at', ''),
                        'time': self._get_time_from_datetime(segment.get('arrival', {}).get('at', ''))
                    },
                    'carrierCode': segment.get('carrierCode', ''),
                    'number': segment.get('number', ''),
                    'aircraft': segment.get('aircraft', {}).get('code', ''),
                    'duration': self._format_duration(segment.get('duration', '')),
                    'airline_logo': self._get_airline_logo(segment.get('carrierCode', ''))
                }
                itinerary_data['segments'].append(segment_data)
            
            if len(itinerary_data['segments']) > 1:
                itinerary_data['connection_time'] = self._calculate_connection_time(
                    itinerary.get('duration', ''),
                    [seg.get('duration', '') for seg in itinerary.get('segments', [])]
                )
            
            processed_offer['itineraries'].append(itinerary_data)
        
        return processed_offer
    
    def _get_airline_logo(self, carrier_code):
        """Get airline logo URL from carrier code."""
        return f"https://s1.apideeplink.com/images/airlines/{carrier_code}.png"
    
    def _get_time_from_datetime(self, datetime_str):
        """Extract time from datetime string."""
        if not datetime_str:
            return ''
        try:
            return datetime.strptime(datetime_str[0:19], "%Y-%m-%dT%H:%M:%S").strftime("%H:%M")
        except ValueError:
            return ''
    
    def _format_duration(self, duration_str):
        """Format duration string from PT format to readable format."""
        if not duration_str:
            return ''
        
        duration_clean = duration_str.replace('PT', '')
        
        hours = 0
        minutes = 0
        
        if 'H' in duration_clean:
            hours_match = re.search(r'(\d+)H', duration_clean)
            if hours_match:
                hours = int(hours_match.group(1))
        
        if 'M' in duration_clean:
            minutes_match = re.search(r'(\d+)M', duration_clean)
            if minutes_match:
                minutes = int(minutes_match.group(1))
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return duration_str
    
    def _calculate_connection_time(self, total_duration, segment_durations):
        """Calculate connection time for multi-segment flights."""
        try:
            def parse_duration(duration_str):
                """Parse PT duration string to minutes."""
                if not duration_str:
                    return 0
                
                duration_clean = duration_str.replace('PT', '')
                total_minutes = 0
                
                if 'H' in duration_clean:
                    hours_match = re.search(r'(\d+)H', duration_clean)
                    if hours_match:
                        total_minutes += int(hours_match.group(1)) * 60
                
                if 'M' in duration_clean:
                    minutes_match = re.search(r'(\d+)M', duration_clean)
                    if minutes_match:
                        total_minutes += int(minutes_match.group(1))
                
                return total_minutes
            
            total_minutes = parse_duration(total_duration)
            segment_minutes = sum(parse_duration(duration) for duration in segment_durations)
            
            connection_minutes = total_minutes - segment_minutes
            
            if connection_minutes > 0:
                hours = connection_minutes // 60
                minutes = connection_minutes % 60
                if hours > 0 and minutes > 0:
                    return f"{hours}h {minutes}m"
                elif hours > 0:
                    return f"{hours}h"
                else:
                    return f"{minutes}m"
            
            return "0m"
            
        except Exception:
            return "Unknown"
    
    def compare_routes(self, origins, destinations, departure_date):
        """
        Compare multiple route options.
        
        Args:
            origins (list): List of origin airport codes
            destinations (list): List of destination airport codes  
            departure_date (str): Departure date (YYYY-MM-DD)
        
        Returns:
            dict: Comparison results for all route combinations
        """
        print(f"🔄 Comparing routes for {departure_date}")
        
        route_comparisons = []
        
        for origin in origins:
            for destination in destinations:
                if origin != destination:
                    print(f"  Checking {origin} → {destination}...")
                    
                    try:
                        results = self._search_single_date(origin, destination, departure_date, None, 1, 1, False)
                        
                        if 'error' not in results and results['flights']:
                            flight = results['flights'][0]
                            route_info = {
                                'route': f"{origin} → {destination}",
                                'origin': origin,
                                'destination': destination,
                                **self._extract_flight_summary(flight, departure_date)
                            }
                            del route_info['date']  # Remove date from route comparison
                            route_comparisons.append(route_info)
                        else:
                            route_comparisons.append({
                                'route': f"{origin} → {destination}",
                                'origin': origin,
                                'destination': destination,
                                'error': 'No flights found'
                            })
                            
                    except Exception as e:
                        route_comparisons.append({
                            'route': f"{origin} → {destination}",
                            'origin': origin,
                            'destination': destination,
                            'error': str(e)
                        })
        
        valid_routes = [r for r in route_comparisons if 'price' in r]
        valid_routes.sort(key=lambda x: x['price'])
        
        return {
            'search_date': departure_date,
            'total_routes_checked': len(route_comparisons),
            'valid_routes': len(valid_routes),
            'route_comparisons': valid_routes,
            'errors': [r for r in route_comparisons if 'error' in r]
        }
    
    def print_price_summary(self, results):
        """Print a formatted price summary."""
        if 'cheapest_flights' in results:
            flights = results['cheapest_flights']
            print(f"\n💰 PRICE SUMMARY")
            print(f"Cheapest: {flights[0]['price']} {flights[0]['currency']} on {flights[0]['date']}")
            print(f"Most expensive: {flights[-1]['price']} {flights[-1]['currency']} on {flights[-1]['date']}")
            
            avg_price = sum(f['price'] for f in flights) / len(flights)
            print(f"Average price: {avg_price:.2f} {flights[0]['currency']}")
        
        elif 'route_comparisons' in results:
            routes = results['route_comparisons']
            if routes:
                print(f"\n💰 ROUTE PRICE COMPARISON")
                for route in routes[:5]:
                    if 'price' in route:
                        print(f"{route['route']}: {route['price']} {route['currency']}")


# Location class for subType parameter (fallback if not available)
try:
    from amadeus import Location
except ImportError:
    class Location:
        AIRPORT = 'AIRPORT'
        CITY = 'CITY' 
        ANY = None


# if __name__ == "__main__":
#     # Example usage of the consolidated AmadeusAgent
#     agent_class = AmadeusAgent()
    
#     # # Quick flight search
#     # results = agent.search_flights("PAR", "NYC", "tomorrow", quick_search=True)
#     # print(f'\n\nQuickSearch Results:\n{results}\n\n')
    
#     # # Find cheapest flights over 7 days
#     # cheapest = agent.search_flights("PAR", "NYC", "2025-12-01", find_cheapest=True, date_range_days=7)
#     # print(f'\n\nCheapSearch Results:\n{cheapest}\n\n')

#     # # Compare multiple routes
#     # comparison = agent.compare_routes(["PAR", "CDG"], ["NYC", "JFK"], "2025-12-01")
#     # print(f'\n\nComparisionSearch Results:\n{comparison}\n\n')
 
#     # # Search airports and get alternatives
#     # alternatives = agent.suggest_alternative_airports("Paris")
#     # print(f'\n\nAlternativesSearch Results:\n{alternatives}\n\n')

#     agent : Agent = agent_class.agent

#     agent.print_response('Can you find me availabe flights from New York To Sanfrancisco for 1 adult on 10-08-2025 ??')

    