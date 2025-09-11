from typing import List, Dict, Any, Optional
from services.gemini_service import GeminiService, RecommendationResult, PlaceDetails
from services.maps_service import MapsService, Coordinates, RouteInfo, Place
from database.database_manager import DatabaseManager
# from services.email_service import EmailService # Kaldırıldı
import json

class RecommendationEngine:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.maps_service = MapsService()
        self.db_manager = DatabaseManager()
        # self.email_service = EmailService() # Yeni servis

    def get_travel_recommendations(self, query: str, user_session_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[RecommendationResult]:
        # Construct a unique cache key based on query and filters
        cache_key = f"{query}_{json.dumps(filters, sort_keys=True)}"
        # 1. Cache Kontrolü
        cached_results = self.db_manager.get_cached_results(cache_key)
        if cached_results:
            print(f"Cache hit for query: {cache_key}")
            # Convert raw JSON back to RecommendationResult objects
            recs = []
            for item in cached_results.get("recommendations", []):
                recs.append(RecommendationResult(
                    title=item["title"],
                    description=item["description"],
                    rating=item["rating"],
                    category=item["category"],
                    location=item.get("location", {})
                ))
            return recs

        print(f"Cache miss for query: {cache_key}. Generating new recommendations.")
        # 2. AI İşleme (Gemini API)
        # Dynamically build the prompt with filters
        prompt_with_filters = f"Bir kullanıcı şu anda bir seyahat önerisi arıyor: '{query}'."
        if filters:
            if filters.get("category") and filters["category"] != "Tümü":
                prompt_with_filters += f" Kategori: {filters['category']}."
            if filters.get("rating") and filters["rating"] > 0:
                prompt_with_filters += f" Minimum puan: {filters['rating']}."
            if filters.get("features"): # Assuming features is a list of strings
                prompt_with_filters += f" Ek özellikler: {', '.join(filters['features'])}."
            # Distance filter can be used for maps_service later, not directly for Gemini prompt for now.
        
        prompt_with_filters += f" Lütfen bu sorguya göre 3 adet seyahat yeri önerisi yapın."
        prompt_with_filters += f" Her öneri için bir başlık (title), kısa bir açıklama (description), 1 ile 5 arasında bir puan (rating), bir kategori (category) ve tahmini enlem (latitude) ve boylam (longitude) içeren bir konum (location) bilgisi sağlayın."
        example_json = [{
            "title": "Yer Adı", 
            "description": "Kısa Açıklama", 
            "rating": 4.5, 
            "category": "Kategori", 
            "location": {"lat": 12.34, "lng": 56.78}
        }]
        example_json_str = json.dumps(example_json, ensure_ascii=False)

        prompt_with_filters += f" JSON formatında bir liste olarak çıktı verin."
        prompt_with_filters += f" Örnek JSON formatı: {example_json_str}"

        recommendations = self.gemini_service.generate_recommendations(prompt_with_filters)
        
        results_to_cache = []
        for rec in recommendations:
            print(f"DEBUG: Recommendation from Gemini - Title: '{rec.title}', Initial Location: {rec.location}") # DEBUG

            # 3. Lokasyon İşleme (Google Maps API) - Koordinatları Al
            coords = None # Koordinatları varsayılan olarak None olarak ayarla
            if not rec.location.get("lat") or not rec.location.get("lng"):
                coords = self.maps_service.get_place_coordinates(rec.title)
                if coords:
                    rec.location = {"lat": coords.latitude, "lng": coords.longitude}
            else:
                # Gemini'den konum geliyorsa, direkt olarak kullan
                coords = Coordinates(latitude=rec.location["lat"], longitude=rec.location["lng"])
            
            print(f"DEBUG: Processing recommendation '{rec.title}'. Final Location: {rec.location}") # DEBUG

            # 3.5 Görsel İşleme (Google Places API) - Fotoğraf URL'lerini Al
            image_urls = self.maps_service.get_place_photos(rec.title)
            print(f"DEBUG: Retrieved {len(image_urls)} image URLs for '{rec.title}'.") # DEBUG

            # Her durumda yer detaylarını places_cache'e kaydet (veya güncelle)
            self.db_manager.save_place_to_cache(
                place_name=rec.title,
                latitude=rec.location.get("lat"), # None olabilir
                longitude=rec.location.get("lng"), # None olabilir
                description=rec.description,
                category=rec.category,
                rating=rec.rating,
                image_urls=image_urls # Yeni eklendi
            )
            print(f"DEBUG: Attempted to save '{rec.title}' to cache with location: {rec.location.get('lat')}, {rec.location.get('lng')}, images: {len(image_urls) if image_urls else 0}") # DEBUG

            results_to_cache.append(rec.__dict__)

        # 4. Veri Kaydetme (arama geçmişi için)
        self.db_manager.save_search_result(cache_key, {"recommendations": results_to_cache}, user_session_id)
        
        return recommendations

    def get_place_details(self, place_name: str) -> Optional[PlaceDetails]:
        # 1. Cache Kontrolü
        cached_details = self.db_manager.get_cached_place_details(place_name)
        if cached_details:
            print(f"Cache hit for place details: {place_name}")
            return PlaceDetails(
                name=place_name,
                latitude=cached_details["latitude"],
                longitude=cached_details["longitude"],
                description=cached_details["description"],
                category=cached_details["category"],
                rating=cached_details["rating"]
            )
        
        print(f"Cache miss for place details: {place_name}. Fetching new details.")
        # Fetch details from Gemini (or another source if available)
        details = self.gemini_service.get_place_details(place_name)
        if details:
            # Save to cache
            self.db_manager.save_place_to_cache(
                name=details.name,
                latitude=details.latitude,
                longitude=details.longitude,
                description=details.description,
                category=details.category,
                rating=details.rating
            )
        return details

    def plan_route(self, places: List[str]) -> Optional[RouteInfo]:
        return self.maps_service.generate_route(places)

    def add_favorite(self, user_session_id: str, place_name: str) -> bool:
        return self.db_manager.add_to_favorites(user_session_id, place_name)

    def get_favorites(self, user_session_id: str) -> List[str]:
        return self.db_manager.get_favorites(user_session_id)

    def remove_favorite(self, user_session_id: str, place_name: str) -> bool:
        return self.db_manager.remove_from_favorites(user_session_id, place_name)

    # def send_travel_plan_email(self, user_email: str, city: str, recommendations: List[Dict[str, Any]]) -> bool:
    #     subject = f"{city} için Akıllı Gezi Planınız"
    #     email_body = self.email_service.format_travel_plan_for_email(city, recommendations)
    #     return self.email_service.send_email(user_email, subject, email_body, is_html=True)

