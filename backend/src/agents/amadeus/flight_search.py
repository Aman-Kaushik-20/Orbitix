import re
from datetime import datetime
from amadeus import Client, ResponseError


def search_flights(origin, destination, departure_date, return_date=None, adults=1, max_results=50):
    """
    Search for available flights based on given parameters.
    
    Args:
        origin (str): Origin airport IATA code (e.g., 'PAR')
        destination (str): Destination airport IATA code (e.g., 'NYC')
        departure_date (str): Departure date in YYYY-MM-DD format
        return_date (str, optional): Return date in YYYY-MM-DD format for round trip
        adults (int): Number of adult passengers (default: 1)
        max_results (int): Maximum number of flight offers to return (default: 50)
    
    Returns:
        dict: Dictionary containing flight offers and trip information
    """
    try:
        # Initialize Amadeus client
        amadeus = Client()
        
        # Prepare search parameters
        search_params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": max_results
        }
        
        # Add return date for round trip
        if return_date:
            search_params["returnDate"] = return_date
        
        # Search for flights
        flight_response = amadeus.shopping.flight_offers_search.get(**search_params)
        
        # Process flight data
        processed_flights = []
        for flight_offer in flight_response.data:
            processed_flight = process_flight_offer(flight_offer)
            processed_flights.append(processed_flight)
        
        # Prepare response
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
        
        # Add trip purpose prediction for round trips
        if return_date:
            try:
                trip_purpose_params = {
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDate": departure_date,
                    "returnDate": return_date,
                }
                trip_purpose_response = amadeus.travel.predictions.trip_purpose.get(**trip_purpose_params)
                result['trip_purpose'] = trip_purpose_response.data.get('result', 'UNKNOWN')
            except ResponseError:
                result['trip_purpose'] = 'UNKNOWN'
        
        return result
        
    except ResponseError as error:
        print(f"Amadeus API Error: {error}")
        return {'error': str(error), 'flights': []}
    except Exception as e:
        print(f"Error searching flights: {e}")
        return {'error': str(e), 'flights': []}


def process_flight_offer(flight_offer):
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
    
    # Process each itinerary (outbound/return)
    for idx, itinerary in enumerate(flight_offer.get('itineraries', [])):
        itinerary_data = {
            'type': 'outbound' if idx == 0 else 'return',
            'duration': format_duration(itinerary.get('duration', '')),
            'segments': []
        }
        
        # Process segments in each itinerary
        for segment in itinerary.get('segments', []):
            segment_data = {
                'departure': {
                    'iataCode': segment.get('departure', {}).get('iataCode', ''),
                    'terminal': segment.get('departure', {}).get('terminal', ''),
                    'at': segment.get('departure', {}).get('at', ''),
                    'time': get_time_from_datetime(segment.get('departure', {}).get('at', ''))
                },
                'arrival': {
                    'iataCode': segment.get('arrival', {}).get('iataCode', ''),
                    'terminal': segment.get('arrival', {}).get('terminal', ''),
                    'at': segment.get('arrival', {}).get('at', ''),
                    'time': get_time_from_datetime(segment.get('arrival', {}).get('at', ''))
                },
                'carrierCode': segment.get('carrierCode', ''),
                'number': segment.get('number', ''),
                'aircraft': segment.get('aircraft', {}).get('code', ''),
                'duration': format_duration(segment.get('duration', '')),
                'airline_logo': get_airline_logo(segment.get('carrierCode', ''))
            }
            itinerary_data['segments'].append(segment_data)
        
        # Calculate connection time for multi-segment flights
        if len(itinerary_data['segments']) > 1:
            itinerary_data['connection_time'] = calculate_connection_time(
                itinerary.get('duration', ''),
                [seg.get('duration', '') for seg in itinerary.get('segments', [])]
            )
        
        processed_offer['itineraries'].append(itinerary_data)
    
    return processed_offer


def get_airline_logo(carrier_code):
    """Get airline logo URL from carrier code."""
    return f"https://s1.apideeplink.com/images/airlines/{carrier_code}.png"


def get_time_from_datetime(datetime_str):
    """Extract time from datetime string."""
    if not datetime_str:
        return ''
    try:
        return datetime.strptime(datetime_str[0:19], "%Y-%m-%dT%H:%M:%S").strftime("%H:%M")
    except ValueError:
        return ''


def format_duration(duration_str):
    """Format duration string from PT format to readable format."""
    if not duration_str:
        return ''
    
    # Remove PT prefix and parse hours and minutes
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


def calculate_connection_time(total_duration, segment_durations):
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


if __name__ == "__main__":
    # Example usage
    print("Testing flight search...")
    
    # Search for one-way flights
    print("\nSearching for one-way flights from PAR to NYC...")
    results = search_flights(
        origin="PAR",
        destination="NYC", 
        departure_date="2025-12-01"
    )
    
    if 'error' not in results:
        print(f"Found {results['total_results']} flights")
        
        # Show first flight details
        if results['flights']:
            first_flight = results['flights'][0]
            print(f"\nFirst flight:")
            print(f"Price: {first_flight['price']['total']} {first_flight['price']['currency']}")
            print(f"Outbound: {len(first_flight['itineraries'][0]['segments'])} segment(s)")
            
            for segment in first_flight['itineraries'][0]['segments']:
                print(f"  {segment['departure']['iataCode']} -> {segment['arrival']['iataCode']}")
                print(f"  Departure: {segment['departure']['time']}, Arrival: {segment['arrival']['time']}")
                print(f"  Carrier: {segment['carrierCode']}, Duration: {segment['duration']}")
    else:
        print(f"Error: {results['error']}")