import os
import requests
from dotenv import load_dotenv

success = load_dotenv(dotenv_path='backend/.env')
if not success:
    raise ValueError(f"Please correct .env path")

api_key = os.getenv("DISTANCE_MATRIX_API_KEY")


geocode_url = "https://api.distancematrix.ai/maps/api/geocode/json"

def geocode_address(address):
    params = {
        'address': address,
        'key': api_key
    }
    
    response = requests.get(geocode_url, params=params).json()
    print(response)
    location = response['result'][0]['geometry']['location']
    
    return location['lat'], location['lng']



distance_url = "https://api.distancematrix.ai/maps/api/distancematrix/json"

def get_time_distance(origins, destinations):
    # origins and destinations should be lists of "lat,lng" strings
    params = {
        'origins': '|'.join(origins),
        'destinations': '|'.join(destinations),
        'key': api_key
    }
    
    response = requests.get(distance_url, params=params).json()
    return response

# Example: Check travel times between multiple drivers and one passenger



# Example: Convert a passenger's address into coordinates
passenger_lat, passenger_lng = geocode_address("Rajiv Chowk Metro Station, Delhi")

driver_lat, driver_lng = geocode_address("Vishwavidyala Metro Station, Delhi")



passenger_coord = [f"{passenger_lat},{passenger_lng}"]
driver_coords = [f'{driver_lat},{driver_lng}']

print('passenger_coord:',passenger_coord)
matrix_data = get_time_distance(driver_coords, passenger_coord)
print('matrix_data:', matrix_data)




'''
{'result': [{'address_components': None, 'formatted_address': '', 'geometry': {'location': {'lat': 28.63273535, 'lng': 77.218879}, 'location_type': 'APPROXIMATE', 'viewport': {'northeast': {'lat': 28.63273535, 'lng': 77.218879}, 'southwest': {'lat': 28.63273535, 'lng': 77.218879}}}, 'place_id': '', 'plus_code': {}, 'types': ['locality', 'political']}], 'status': 'OK'}
{'result': [{'address_components': None, 'formatted_address': '', 'geometry': {'location': {'lat': 28.695190000000004, 'lng': 77.21450999999999}, 'location_type': 'APPROXIMATE', 'viewport': {'northeast': {'lat': 28.695190000000004, 'lng': 77.21450999999999}, 'southwest': {'lat': 28.695190000000004, 'lng': 77.21450999999999}}}, 'place_id': 'ChIJzxqojer9DDkRwDFotgLcFkk', 'plus_code': {}, 'types': ['locality', 'political']}], 'status': 'OK'}
passenger_coord: ['28.63273535,77.218879']
matrix_data: {'destination_addresses': ['OYO 363 Hotel The W, Plot No.G-68, Near Metro Exit 7 & 8, Outer Circle, Connaught Place, Delhi, 110001, India'], 'origin_addresses': ['Mahatma Gandhi Marg, Banarsi Das Estate, Timarpur, Delhi, 110054, India'], 'rows': [{'elements': [{'distance': {'text': '10.3 km', 'value': 10266}, 'duration': {'text': '29 mins', 'value': 1794}, 'origin': '28.695190000000004,77.21450999999999', 'destination': '28.63273535,77.218879', 'status': 'OK'}]}], 'status': 'OK'}
'''