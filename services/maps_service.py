import googlemaps
from typing import List, Dict, Any, Optional

from config.api_keys import GOOGLE_MAPS_API_KEY

# Placeholder for data structures
class Coordinates:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

class Place:
    def __init__(self, name: str, latitude: float, longitude: float, description: str, category: str, rating: float):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.category = category
        self.rating = rating

class RouteInfo:
    def __init__(self, distance: str, duration: str, steps: List[str]):
        self.distance = distance
        self.duration = duration
        self.steps = steps

class MapsService:
    def __init__(self):
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API Key is not set in environment variables.")
        self.client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        
    def get_place_coordinates(self, place_name: str) -> Optional[Coordinates]:
        try:
            print(f"DEBUG: MapsService geocoding for: {place_name}") # DEBUG
            geocode_result = self.client.geocode(place_name)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                print(f"DEBUG: MapsService found coordinates for {place_name}: {location}") # DEBUG
                return Coordinates(latitude=location['lat'], longitude=location['lng'])
            print(f"DEBUG: MapsService found no results for: {place_name}") # DEBUG
            return None
        except Exception as e:
            print(f"Error getting place coordinates with Google Maps API for {place_name}: {e}") # DEBUG
            return None

    def get_place_photos(self, place_name: str, max_width: int = 400) -> List[str]:
        try:
            # First, find the place_id using places API text search
            places_result = self.client.places(query=place_name)
            if not places_result or not places_result.get('results'):
                print(f"DEBUG: No place results found for photos of {place_name}.")
                return []
            
            place_id = places_result['results'][0]['place_id']
            
            # Then, get place details including photo references
            details_result = self.client.place(place_id=place_id, fields=['photos'])
            
            photo_references = []
            if details_result and details_result.get('result') and details_result['result'].get('photos'):
                for photo in details_result['result']['photos']:
                    photo_references.append(photo['photo_reference'])
            
            photo_urls = []
            for ref in photo_references:
                # Construct photo URL
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={ref}&key={GOOGLE_MAPS_API_KEY}"
                photo_urls.append(photo_url)
            
            print(f"DEBUG: Found {len(photo_urls)} photos for {place_name}.")
            return photo_urls
        except Exception as e:
            print(f"Error getting place photos with Google Maps API for {place_name}: {e}")
            return []

    def generate_route(self, places: List[str]) -> Optional[RouteInfo]:
        if len(places) < 2:
            return None
        try:
            directions_result = self.client.directions(
                origin=places[0],
                destination=places[-1],
                mode="driving",
                waypoints=places[1:-1] if len(places) > 2 else None
            )
            if directions_result:
                route = directions_result[0]['legs'][0]
                distance = route['distance']['text']
                duration = route['duration']['text']
                steps = [step['html_instructions'] for step in route['steps']]
                return RouteInfo(distance=distance, duration=duration, steps=steps)
            return None
        except Exception as e:
            print(f"Error generating route with Google Maps API: {e}")
            return None

    def get_travel_time_minutes(self, origin: Coordinates, destination: Coordinates, mode: str = "driving") -> Optional[int]:
        """Estimate travel time in minutes between two coordinates for a given mode (driving, walking, transit)."""
        try:
            if mode not in ["driving", "walking", "transit", "bicycling"]:
                mode = "driving"
            directions = self.client.directions(
                origin=(origin.latitude, origin.longitude),
                destination=(destination.latitude, destination.longitude),
                mode=mode
            )
            if not directions:
                return None
            leg = directions[0]['legs'][0]
            seconds = leg['duration']['value']
            return int(round(seconds / 60))
        except Exception as e:
            print(f"Error getting travel time: {e}")
            return None

