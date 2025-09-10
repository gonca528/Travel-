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
            geocode_result = self.client.geocode(place_name)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return Coordinates(latitude=location['lat'], longitude=location['lng'])
            return None
        except Exception as e:
            print(f"Error getting place coordinates with Google Maps API: {e}")
            return None

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

    def get_nearby_places(self, lat: float, lng: float, radius: int = 5000, keyword: Optional[str] = None) -> List[Place]:
        try:
            places_result = self.client.places_nearby(
                location=(lat, lng),
                radius=radius,
                keyword=keyword
            )
            nearby_places = []
            for p in places_result['results']:
                name = p.get('name', '')
                place_lat = p['geometry']['location']['lat']
                place_lng = p['geometry']['location']['lng']
                # Google Places API does not directly provide a 'description' or 'category' in nearby search results
                # and rating is optional. We'll use dummy or default values for now.
                rating = p.get('rating', 0.0)
                category = p.get('types', [''])[0].replace('_', ' ').title() # Take the first type as category
                description = f"A {category} located nearby." # Placeholder description

                nearby_places.append(Place(
                    name=name,
                    latitude=place_lat,
                    longitude=place_lng,
                    description=description,
                    category=category,
                    rating=rating
                ))
            return nearby_places
        except Exception as e:
            print(f"Error getting nearby places with Google Maps API: {e}")
            return []

