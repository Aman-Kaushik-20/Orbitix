# Amadeus Flight Search API

Independent Python backend for airport and flight search functionality using the Amadeus API.

## Features

1. **Airport Search** - Search for airports by keyword (city name, airport name, or IATA code)
2. **Flight Search** - Search for available flights based on origin, destination, and dates

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Amadeus API credentials as environment variables:
```bash
export AMADEUS_CLIENT_ID="your_client_id"
export AMADEUS_CLIENT_SECRET="your_client_secret"
```

## Usage

### Airport Search

```python
from copied_amadeus import search_airports, get_airport_details

# Search for airports by keyword
airports = search_airports("Paris")
for airport in airports:
    print(f"{airport['name']} ({airport['iataCode']}) - {airport['cityName']}")

# Get specific airport details
cdg_info = get_airport_details("CDG")
print(f"Airport: {cdg_info['name']}")
```

### Flight Search

```python
from copied_amadeus import search_flights

# One-way flight search
flights = search_flights(
    origin="PAR",
    destination="NYC", 
    departure_date="2025-12-01"
)

# Round-trip flight search
round_trip_flights = search_flights(
    origin="PAR",
    destination="NYC",
    departure_date="2025-12-01",
    return_date="2025-12-08"
)

print(f"Found {flights['total_results']} flights")
for flight in flights['flights'][:5]:  # Show first 5 flights
    print(f"Price: {flight['price']['total']} {flight['price']['currency']}")
```

## API Functions

### `search_airports(keyword, max_results=20)`
- **keyword**: Search term (city name, airport name, or IATA code)
- **max_results**: Maximum number of results (default: 20)
- **Returns**: List of airport dictionaries with name, iataCode, cityName, etc.

### `get_airport_details(iata_code)`
- **iata_code**: 3-letter IATA airport code
- **Returns**: Detailed airport information dictionary

### `search_flights(origin, destination, departure_date, return_date=None, adults=1, max_results=50)`
- **origin**: Origin airport IATA code
- **destination**: Destination airport IATA code  
- **departure_date**: Departure date (YYYY-MM-DD format)
- **return_date**: Return date for round trip (optional)
- **adults**: Number of adult passengers (default: 1)
- **max_results**: Maximum flight offers to return (default: 50)
- **Returns**: Dictionary with flight offers and search parameters

## Dependencies

- `amadeus==7.1.0` - Official Amadeus API Python SDK
- `isodate==0.6.0` - For date/time parsing

## Note

This package is independent and does not require Django or any web framework. It can be used in any Python application.