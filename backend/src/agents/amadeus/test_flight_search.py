#!/usr/bin/env python3
"""
Interactive Flight Search Testing Script
Usage: python test_flight_search.py
"""

import sys
from datetime import datetime, timedelta
from flight_search import search_flights


def test_flight_search_interactive():
    """Interactive flight search testing."""
    print("=" * 60)
    print("FLIGHT SEARCH TESTING TOOL")
    print("=" * 60)
    print("Commands:")
    print("  oneway <from> <to> <date>           - One-way flight search")
    print("  roundtrip <from> <to> <dep> <ret>   - Round-trip flight search")
    print("  popular                             - Test popular routes")
    print("  quit                                - Exit")
    print()
    print("Date format: YYYY-MM-DD (e.g., 2025-12-01)")
    print("Airport codes: 3-letter IATA codes (e.g., PAR, NYC, LON)")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nEnter command: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower().startswith('oneway '):
                parts = user_input.split()
                if len(parts) >= 4:
                    origin, destination, date = parts[1], parts[2], parts[3]
                    test_oneway_flight(origin.upper(), destination.upper(), date)
                else:
                    print("Usage: oneway <from> <to> <date>")
                    print("Example: oneway PAR NYC 2025-12-01")
            elif user_input.lower().startswith('roundtrip '):
                parts = user_input.split()
                if len(parts) >= 5:
                    origin, destination, dep_date, ret_date = parts[1], parts[2], parts[3], parts[4]
                    test_roundtrip_flight(origin.upper(), destination.upper(), dep_date, ret_date)
                else:
                    print("Usage: roundtrip <from> <to> <departure_date> <return_date>")
                    print("Example: roundtrip PAR NYC 2025-12-01 2025-12-08")
            elif user_input.lower() == 'popular':
                test_popular_routes()
            elif user_input.lower() in ['help', 'h']:
                print("Commands:")
                print("  oneway <from> <to> <date>           - One-way flight search")
                print("  roundtrip <from> <to> <dep> <ret>   - Round-trip flight search")
                print("  popular                             - Test popular routes")
                print("  quit                                - Exit")
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def test_oneway_flight(origin, destination, departure_date):
    """Test one-way flight search."""
    print(f"\n✈️  ONE-WAY FLIGHT SEARCH")
    print(f"Route: {origin} → {destination}")
    print(f"Date: {departure_date}")
    print("-" * 50)
    
    try:
        results = search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            max_results=5
        )
        
        if 'error' not in results and results['flights']:
            print(f"✅ Found {results['total_results']} flights")
            print(f"Showing first {min(5, len(results['flights']))} results:\n")
            
            for i, flight in enumerate(results['flights'][:5], 1):
                print_flight_summary(flight, i)
                
            # Show detailed info for first flight
            if results['flights']:
                print("\n📋 DETAILED INFO - First Flight:")
                print_flight_details(results['flights'][0])
                
        else:
            error_msg = results.get('error', 'No flights found')
            print(f"❌ {error_msg}")
            
    except Exception as e:
        print(f"❌ Error searching flights: {e}")


def test_roundtrip_flight(origin, destination, departure_date, return_date):
    """Test round-trip flight search."""
    print(f"\n✈️  ROUND-TRIP FLIGHT SEARCH")
    print(f"Route: {origin} ⇄ {destination}")
    print(f"Departure: {departure_date}")
    print(f"Return: {return_date}")
    print("-" * 50)
    
    try:
        results = search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            max_results=3
        )
        
        if 'error' not in results and results['flights']:
            print(f"✅ Found {results['total_results']} round-trip flights")
            print(f"🎯 Trip Purpose: {results.get('trip_purpose', 'UNKNOWN')}")
            print(f"Showing first {min(3, len(results['flights']))} results:\n")
            
            for i, flight in enumerate(results['flights'][:3], 1):
                print_roundtrip_summary(flight, i)
                
            # Show detailed info for first flight
            if results['flights']:
                print("\n📋 DETAILED INFO - First Flight:")
                print_roundtrip_details(results['flights'][0])
                
        else:
            error_msg = results.get('error', 'No flights found')
            print(f"❌ {error_msg}")
            
    except Exception as e:
        print(f"❌ Error searching flights: {e}")


def print_flight_summary(flight, index):
    """Print a summary of a one-way flight."""
    outbound = flight['itineraries'][0]
    segments = outbound['segments']
    
    print(f"Flight {index}:")
    print(f"  💰 Price: {flight['price']['total']} {flight['price']['currency']}")
    print(f"  🕒 Duration: {outbound['duration']}")
    print(f"  🛫 Route: {segments[0]['departure']['iataCode']} → {segments[-1]['arrival']['iataCode']}")
    print(f"  ⏰ Times: {segments[0]['departure']['time']} - {segments[-1]['arrival']['time']}")
    
    if len(segments) > 1:
        print(f"  🔄 Stops: {len(segments) - 1} stop(s)")
        print(f"  ⏳ Connection time: {outbound.get('connection_time', 'N/A')}")
    else:
        print(f"  ✈️  Direct flight")
    
    airlines = [f"{seg['carrierCode']} {seg['number']}" for seg in segments]
    print(f"  🏢 Airlines: {' + '.join(airlines)}")
    print()


def print_roundtrip_summary(flight, index):
    """Print a summary of a round-trip flight."""
    outbound = flight['itineraries'][0]
    return_flight = flight['itineraries'][1]
    
    print(f"Round-trip Flight {index}:")
    print(f"  💰 Total Price: {flight['price']['total']} {flight['price']['currency']}")
    
    # Outbound info
    out_segments = outbound['segments']
    print(f"  🛫 Outbound: {out_segments[0]['departure']['iataCode']} → {out_segments[-1]['arrival']['iataCode']}")
    print(f"     Times: {out_segments[0]['departure']['time']} - {out_segments[-1]['arrival']['time']}")
    print(f"     Duration: {outbound['duration']}")
    
    # Return info
    ret_segments = return_flight['segments']
    print(f"  🛬 Return: {ret_segments[0]['departure']['iataCode']} → {ret_segments[-1]['arrival']['iataCode']}")
    print(f"     Times: {ret_segments[0]['departure']['time']} - {ret_segments[-1]['arrival']['time']}")
    print(f"     Duration: {return_flight['duration']}")
    print()


def print_flight_details(flight):
    """Print detailed flight information."""
    outbound = flight['itineraries'][0]
    
    for i, segment in enumerate(outbound['segments'], 1):
        print(f"  Segment {i}:")
        print(f"    Flight: {segment['carrierCode']} {segment['number']}")
        print(f"    Aircraft: {segment['aircraft']}")
        print(f"    Route: {segment['departure']['iataCode']} → {segment['arrival']['iataCode']}")
        print(f"    Departure: {segment['departure']['time']} (Terminal {segment['departure'].get('terminal', 'N/A')})")
        print(f"    Arrival: {segment['arrival']['time']} (Terminal {segment['arrival'].get('terminal', 'N/A')})")
        print(f"    Duration: {segment['duration']}")
        print()


def print_roundtrip_details(flight):
    """Print detailed round-trip flight information."""
    for itinerary in flight['itineraries']:
        trip_type = itinerary['type'].title()
        print(f"  {trip_type} Journey:")
        print(f"    Duration: {itinerary['duration']}")
        
        for i, segment in enumerate(itinerary['segments'], 1):
            print(f"    Segment {i}:")
            print(f"      Flight: {segment['carrierCode']} {segment['number']}")
            print(f"      Route: {segment['departure']['iataCode']} → {segment['arrival']['iataCode']}")
            print(f"      Times: {segment['departure']['time']} - {segment['arrival']['time']}")
        print()


def test_popular_routes():
    """Test popular flight routes."""
    print("\n🌍 TESTING POPULAR ROUTES")
    print("=" * 50)
    
    # Generate dates for next month
    today = datetime.now()
    next_month = today + timedelta(days=30)
    departure_date = next_month.strftime('%Y-%m-%d')
    return_date = (next_month + timedelta(days=7)).strftime('%Y-%m-%d')
    
    popular_routes = [
        ("PAR", "NYC", "Paris to New York"),
        ("LON", "JFK", "London to JFK"),
        ("FRA", "LAX", "Frankfurt to Los Angeles"),
        ("DXB", "LHR", "Dubai to London"),
        ("SIN", "NRT", "Singapore to Tokyo")
    ]
    
    for origin, destination, description in popular_routes:
        print(f"\n🧪 Testing: {description}")
        print(f"Route: {origin} → {destination}")
        print(f"Date: {departure_date}")
        
        try:
            results = search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                max_results=2
            )
            
            if 'error' not in results and results['flights']:
                print(f"✅ Found {results['total_results']} flights")
                if results['flights']:
                    flight = results['flights'][0]
                    segments = flight['itineraries'][0]['segments']
                    print(f"   Best price: {flight['price']['total']} {flight['price']['currency']}")
                    print(f"   Duration: {flight['itineraries'][0]['duration']}")
                    print(f"   Airlines: {segments[0]['carrierCode']} {segments[0]['number']}")
            else:
                print(f"❌ No flights found or error occurred")
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "popular":
            test_popular_routes()
        elif sys.argv[1] == "oneway" and len(sys.argv) >= 5:
            origin, destination, date = sys.argv[2].upper(), sys.argv[3].upper(), sys.argv[4]
            test_oneway_flight(origin, destination, date)
        elif sys.argv[1] == "roundtrip" and len(sys.argv) >= 6:
            origin, destination, dep_date, ret_date = sys.argv[2].upper(), sys.argv[3].upper(), sys.argv[4], sys.argv[5]
            test_roundtrip_flight(origin, destination, dep_date, ret_date)
        else:
            print("Usage:")
            print("  python test_flight_search.py                              # Interactive mode")
            print("  python test_flight_search.py popular                      # Test popular routes")
            print("  python test_flight_search.py oneway PAR NYC 2025-12-01    # Quick one-way search")
            print("  python test_flight_search.py roundtrip PAR NYC 2025-12-01 2025-12-08  # Quick round-trip")
    else:
        test_flight_search_interactive()


if __name__ == "__main__":
    main()