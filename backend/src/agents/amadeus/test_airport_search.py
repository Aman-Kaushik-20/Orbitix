#!/usr/bin/env python3
"""
Interactive Airport Search Testing Script
Usage: python test_airport_search.py
"""

import sys
from airport_search import search_airports, get_airport_details


def test_airport_search_interactive():
    """Interactive airport search testing."""
    print("=" * 60)
    print("AIRPORT SEARCH TESTING TOOL")
    print("=" * 60)
    print("Commands:")
    print("  search <keyword>     - Search for airports")
    print("  details <iata_code>  - Get airport details")
    print("  quit                 - Exit")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nEnter command: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower().startswith('search '):
                keyword = user_input[7:].strip()
                if keyword:
                    test_search(keyword)
                else:
                    print("Please provide a keyword. Example: search Paris")
            elif user_input.lower().startswith('details '):
                iata_code = user_input[8:].strip().upper()
                if iata_code:
                    test_details(iata_code)
                else:
                    print("Please provide an IATA code. Example: details CDG")
            elif user_input.lower() in ['help', 'h']:
                print("Commands:")
                print("  search <keyword>     - Search for airports")
                print("  details <iata_code>  - Get airport details")
                print("  quit                 - Exit")
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def test_search(keyword):
    """Test airport search with a keyword."""
    print(f"\n🔍 Searching for airports with keyword: '{keyword}'")
    print("-" * 50)
    
    try:
        results = search_airports(keyword, max_results=10)
        
        if results:
            print(f"Found {len(results)} airports:")
            for i, airport in enumerate(results, 1):
                print(f"{i:2d}. {airport['name']} ({airport['iataCode']})")
                print(f"    📍 {airport['cityName']}, {airport['countryName']}")
                print(f"    🏷️  Type: {airport['subType']}")
                print()
        else:
            print("❌ No airports found.")
            
    except Exception as e:
        print(f"❌ Error searching airports: {e}")


def test_details(iata_code):
    """Test airport details retrieval."""
    print(f"\n📋 Getting details for airport: {iata_code}")
    print("-" * 50)
    
    try:
        details = get_airport_details(iata_code)
        
        if details:
            print(f"✅ Airport Details:")
            print(f"   Name: {details['name']}")
            print(f"   IATA Code: {details['iataCode']}")
            print(f"   City: {details['cityName']}")
            print(f"   Country: {details['countryName']}")
            print(f"   Type: {details['subType']}")
            print(f"   Time Zone: {details.get('timeZone', 'N/A')}")
            
            if details.get('geoCode'):
                lat = details['geoCode'].get('latitude', 'N/A')
                lng = details['geoCode'].get('longitude', 'N/A')
                print(f"   Coordinates: {lat}, {lng}")
        else:
            print(f"❌ No details found for airport code: {iata_code}")
            
    except Exception as e:
        print(f"❌ Error getting airport details: {e}")


def run_preset_tests():
    """Run predefined tests."""
    print("=" * 60)
    print("PRESET AIRPORT SEARCH TESTS")
    print("=" * 60)
    
    test_cases = [
        # City names
        ("Paris", "Search by city name"),
        ("London", "Search by city name"),
        ("Tokyo", "Search by city name"),
        
        # Airport codes
        ("CDG", "Search by IATA code"),
        ("JFK", "Search by IATA code"),
        ("LHR", "Search by IATA code"),
        
        # Partial matches
        ("New York", "Search by city name with space"),
        ("Los", "Partial city name search")
    ]
    
    for keyword, description in test_cases:
        print(f"\n🧪 Test: {description}")
        test_search(keyword)
        print()
    
    # Test airport details
    detail_tests = ["CDG", "JFK", "LHR", "NRT", "DXB"]
    print("\n" + "=" * 60)
    print("AIRPORT DETAILS TESTS")
    print("=" * 60)
    
    for iata_code in detail_tests:
        test_details(iata_code)
        print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "auto":
            run_preset_tests()
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            keyword = " ".join(sys.argv[2:])
            test_search(keyword)
        elif sys.argv[1] == "details" and len(sys.argv) > 2:
            iata_code = sys.argv[2].upper()
            test_details(iata_code)
        else:
            print("Usage:")
            print("  python test_airport_search.py                    # Interactive mode")
            print("  python test_airport_search.py auto               # Run preset tests")
            print("  python test_airport_search.py search <keyword>   # Quick search")
            print("  python test_airport_search.py details <iata>     # Quick details")
    else:
        test_airport_search_interactive()


if __name__ == "__main__":
    main()