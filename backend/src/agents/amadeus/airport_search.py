from amadeus import Client, ResponseError


def search_airports(keyword, max_results=20):
    """
    Search for airports based on a keyword (city name, airport name, or IATA code).
    
    Args:
        keyword (str): Search keyword (e.g., 'PAR', 'Paris', 'London')
        max_results (int): Maximum number of results to return (default: 20)
    
    Returns:
        list: List of airport dictionaries with name, iataCode, and cityName
    """
    try:
        # Initialize Amadeus client
        amadeus = Client()
        
        # Search for airports using Amadeus API
        response = amadeus.reference_data.locations.get(
            keyword=keyword,
            subType=Location.ANY,
            page={'limit': max_results}
        )
        
        # Process and format the results
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


def get_airport_details(iata_code):
    """
    Get detailed information about a specific airport using its IATA code.
    
    Args:
        iata_code (str): 3-letter IATA airport code (e.g., 'CDG')
    
    Returns:
        dict: Detailed airport information or None if not found
    """
    try:
        amadeus = Client()
        
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


# Import Location class for subType parameter
try:
    from amadeus import Location
except ImportError:
    # Fallback if Location is not available in the current version
    class Location:
        AIRPORT = 'AIRPORT'
        CITY = 'CITY' 
        ANY = None


if __name__ == "__main__":
    # Example usage
    print("Testing airport search...")
    
    # Search for Paris airports
    results = search_airports("Paris")
    print(f"\nFound {len(results)} airports for 'Paris':")
    for airport in results[:5]:  # Show first 5 results
        print(f"- {airport['name']} ({airport['iataCode']}) - {airport['cityName']}, {airport['countryName']}")
    
    # Get details for a specific airport
    print("\nGetting details for CDG airport...")
    cdg_details = get_airport_details("CDG")
    if cdg_details:
        print(f"Airport: {cdg_details['name']}")
        print(f"City: {cdg_details['cityName']}, {cdg_details['countryName']}")
        print(f"IATA Code: {cdg_details['iataCode']}")