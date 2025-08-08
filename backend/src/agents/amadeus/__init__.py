"""
Amadeus Flight Search API
Independent Python backend for airport and flight search functionality.
"""

from .airport_search import search_airports, get_airport_details
from .flight_search import search_flights

__version__ = "1.0.0"
__all__ = ["search_airports", "get_airport_details", "search_flights"]