#!/usr/bin/env python3
"""
Utility functions for Amadeus Flight Search API
Common operations and helper functions for easier usage.
"""

import json
import csv
from datetime import datetime, timedelta
from airport_search import search_airports, get_airport_details
from flight_search import search_flights


class FlightSearchHelper:
    """Helper class for common flight search operations."""
    
    def __init__(self):
        self.cached_airports = {}
    
    def find_cheapest_flights(self, origin, destination, date_range_days=7, departure_date=None):
        """
        Find cheapest flights within a date range.
        
        Args:
            origin (str): Origin airport code
            destination (str): Destination airport code
            date_range_days (int): Number of days to search from departure_date
            departure_date (str): Starting date (YYYY-MM-DD), defaults to tomorrow
        
        Returns:
            dict: Best flights found with pricing information
        """
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
                results = search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=search_date,
                    max_results=3
                )
                
                if 'error' not in results and results['flights']:
                    for flight in results['flights'][:1]:  # Take best flight of the day
                        flight_info = {
                            'date': search_date,
                            'price': float(flight['price']['total']),
                            'currency': flight['price']['currency'],
                            'duration': flight['itineraries'][0]['duration'],
                            'flight_id': flight['id'],
                            'segments': len(flight['itineraries'][0]['segments']),
                            'airline': flight['itineraries'][0]['segments'][0]['carrierCode']
                        }
                        best_flights.append(flight_info)
                        
            except Exception as e:
                print(f"    Error for {search_date}: {e}")
        
        # Sort by price
        best_flights.sort(key=lambda x: x['price'])
        
        return {
            'search_params': {
                'origin': origin,
                'destination': destination,
                'date_range': f"{departure_date} to {date_range_days} days",
                'total_dates_checked': len(best_flights)
            },
            'cheapest_flights': best_flights[:5],  # Top 5 cheapest
            'price_range': {
                'min': min(best_flights, key=lambda x: x['price'])['price'] if best_flights else 0,
                'max': max(best_flights, key=lambda x: x['price'])['price'] if best_flights else 0
            }
        }
    
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
                        results = search_flights(
                            origin=origin,
                            destination=destination,
                            departure_date=departure_date,
                            max_results=1
                        )
                        
                        if 'error' not in results and results['flights']:
                            flight = results['flights'][0]
                            route_info = {
                                'route': f"{origin} → {destination}",
                                'origin': origin,
                                'destination': destination,
                                'price': float(flight['price']['total']),
                                'currency': flight['price']['currency'],
                                'duration': flight['itineraries'][0]['duration'],
                                'segments': len(flight['itineraries'][0]['segments']),
                                'airline': flight['itineraries'][0]['segments'][0]['carrierCode']
                            }
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
        
        # Sort by price (valid routes only)
        valid_routes = [r for r in route_comparisons if 'price' in r]
        valid_routes.sort(key=lambda x: x['price'])
        
        return {
            'search_date': departure_date,
            'total_routes_checked': len(route_comparisons),
            'valid_routes': len(valid_routes),
            'route_comparisons': valid_routes,
            'errors': [r for r in route_comparisons if 'error' in r]
        }
    
    def get_airport_info_batch(self, airport_codes):
        """Get information for multiple airports at once."""
        airports_info = {}
        
        for code in airport_codes:
            if code in self.cached_airports:
                airports_info[code] = self.cached_airports[code]
            else:
                try:
                    info = get_airport_details(code)
                    if info:
                        airports_info[code] = info
                        self.cached_airports[code] = info
                    else:
                        airports_info[code] = {'error': 'Airport not found'}
                except Exception as e:
                    airports_info[code] = {'error': str(e)}
        
        return airports_info


def save_results_to_json(results, filename):
    """Save search results to JSON file."""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"💾 Results saved to {filename}")


def save_results_to_csv(results, filename):
    """Save flight results to CSV file."""
    if 'flights' in results:
        flights = results['flights']
    elif 'cheapest_flights' in results:
        flights = results['cheapest_flights']
    elif 'route_comparisons' in results:
        flights = results['route_comparisons']
    else:
        print("❌ No flight data found in results")
        return
    
    if not flights:
        print("❌ No flights to save")
        return
    
    fieldnames = flights[0].keys()
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flights)
    
    print(f"💾 Results saved to {filename}")


def print_price_summary(results):
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
            for route in routes[:5]:  # Show top 5
                if 'price' in route:
                    print(f"{route['route']}: {route['price']} {route['currency']}")


def suggest_alternative_airports(city_keyword):
    """Suggest alternative airports for a city."""
    print(f"🔍 Finding alternative airports for: {city_keyword}")
    
    airports = search_airports(city_keyword, max_results=10)
    
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


# Quick utility functions
def quick_flight_search(origin, destination, date="tomorrow"):
    """Quick flight search with simple parameters."""
    if date == "tomorrow":
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime('%Y-%m-%d')
    
    print(f"✈️  Quick search: {origin} → {destination} on {date}")
    
    results = search_flights(origin, destination, date, max_results=3)
    
    if 'error' not in results and results['flights']:
        print(f"Found {len(results['flights'])} flights:")
        for i, flight in enumerate(results['flights'], 1):
            segments = flight['itineraries'][0]['segments']
            print(f"  {i}. {flight['price']['total']} {flight['price']['currency']} - "
                  f"{segments[0]['departure']['time']} to {segments[-1]['arrival']['time']} "
                  f"({flight['itineraries'][0]['duration']})")
        return results
    else:
        print("❌ No flights found")
        return None


def batch_airport_lookup(airport_codes):
    """Look up multiple airports quickly."""
    helper = FlightSearchHelper()
    return helper.get_airport_info_batch(airport_codes)


if __name__ == "__main__":
    # Example usage
    print("Amadeus Utilities - Example Usage")
    print("=" * 40)
    
    # Quick airport alternatives
    suggest_alternative_airports("Paris")
    
    # Quick flight search
    quick_flight_search("PAR", "LON")
    
    # Batch airport lookup
    codes = ["CDG", "ORY", "LHR", "JFK"]
    airports_info = batch_airport_lookup(codes)
    print(f"\n📍 Airport information:")
    for code, info in airports_info.items():
        if 'error' not in info:
            print(f"  {code}: {info['name']} - {info['cityName']}")
        else:
            print(f"  {code}: {info['error']}")