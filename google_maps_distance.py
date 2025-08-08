import os
import googlemaps
from dotenv import load_dotenv

# Load environment variables from backend/.env
# Make sure your .env file is in a 'backend' directory relative to where you run this script,
# or adjust the path accordingly.
dotenv_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    # If not found, try to load from a .env in the current directory for flexibility.
    load_dotenv()


# Get API key
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file or environment variables.")

# Initialize Google Maps client
gmaps = googlemaps.Client(key=api_key)

def get_distance_matrix(source, destination, mode):
    """
    Calculates distance and travel time between a source and a destination using Google Maps.

    Args:
        source (str): The starting address (e.g., "Eiffel Tower, Paris").
        destination (str): The destination address (e.g., "Louvre Museum, Paris").

    Returns:
        dict: A dictionary containing distance and duration, or None if an error occurs.
              Example: {'distance': '10.3 km', 'duration': '29 mins'}
    """
    try:
        matrix = gmaps.distance_matrix(source, destination, mode=mode)

        # Check if the API call was successful and returned results
        if matrix['status'] == 'OK' and matrix['rows'][0]['elements'][0]['status'] == 'OK':
            distance = matrix['rows'][0]['elements'][0]['distance']['text']
            duration = matrix['rows'][0]['elements'][0]['duration']['text']
            return {
                'distance': distance,
                'duration': duration
            }
        else:
            print(f"Error from API: {matrix.get('error_message', 'Unknown error')}")
            # You can also check matrix['rows'][0]['elements'][0]['status'] for more details
            # e.g., 'NOT_FOUND', 'ZERO_RESULTS'
            element_status = matrix['rows'][0]['elements'][0].get('status')
            print(f"Origin: '{source}', Destination: '{destination}' - Status: {element_status}")
            return None
    except googlemaps.exceptions.ApiError as e:
        print(f"An API error occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    source_address = "Rajiv Chowk Metro Station, Delhi"
    destination_address = "Vishwavidyala Metro Station, Delhi"
    mode="driving"

    result = get_distance_matrix(source_address, destination_address, mode)

    if result:
        print(f"Source: {source_address}")
        print(f"Destination: {destination_address}")
        print(f"Distance: {result['distance']}")
        print(f"Duration: {result['duration']}")

    print("\n" + "="*20 + "\n")

    # # Example that might not find a result
    # source_address_invalid = "asdasdasd, asdasd"
    # destination_address_invalid = "zxczxczxc, zxczxc"
    # invalid_result = get_distance_matrix(source_address_invalid, destination_address_invalid)
    # if not invalid_result:
    #     print("Could not retrieve data for invalid address, as expected.")


'''
    :param mode: Specifies the mode of transport to use when calculating
        directions. Valid values are "driving", "walking", "transit" or
        "bicycling".
'''