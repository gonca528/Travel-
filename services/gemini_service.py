import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json

from config.api_keys import GEMINI_API_KEY

# Placeholder for recommendation results and place details structures
class RecommendationResult:
    def __init__(self, title: str, description: str, rating: float, category: str, location: Dict[str, Any]):
        self.title = title
        self.description = description
        self.rating = rating
        self.category = category
        self.location = location

class PlaceDetails:
    def __init__(self, name: str, latitude: float, longitude: float, description: str, category: str, rating: float):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.category = category
        self.rating = rating

class AIRecommendationService(ABC):
    @abstractmethod
    def generate_recommendations(self, query: str) -> List[RecommendationResult]:
        pass
    
    @abstractmethod
    def get_place_details(self, place_name: str) -> Optional[PlaceDetails]:
        pass

class GeminiService(AIRecommendationService):
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API Key is not set in environment variables.")
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')

    def generate_recommendations(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[RecommendationResult]:
        try:
            prompt_text = f"Bir kullanıcı şu anda bir seyahat önerisi arıyor: '{query}'."
            if filters:
                if filters.get("category") and filters["category"] != "Tümü":
                    prompt_text += f" Öneriler '**{filters['category']}**' kategorisinde olmalıdır."
                if filters.get("rating") and filters["rating"] > 0:
                    prompt_text += f" Önerilerin minimum puanı '**{filters['rating']}**' olmalıdır."
                if filters.get("features"): 
                    prompt_text += f" Önerilerde '**{', '.join(filters['features'])}**' özellikleri bulunmalıdır."
            
            prompt_text += f" Lütfen bu sorguya göre 3 adet seyahat yeri önerisi yapın."
            prompt_text += f" Her öneri için bir başlık (title), kısa bir açıklama (description), 1 ile 5 arasında bir puan (rating), bir kategori (category) ve tahmini enlem (latitude) ve boylam (longitude) içeren bir konum (location) bilgisi sağlayın."
            prompt_text += f" JSON formatında bir liste olarak çıktı verin."
            
            example_json = [{
                "title": "Yer Adı", 
                "description": "Kısa Açıklama", 
                "rating": 4.5, 
                "category": "Kategori", 
                "location": {"lat": 12.34, "lng": 56.78}
            }]
            example_json_str = json.dumps(example_json, ensure_ascii=False)
            prompt_text += f" Örnek JSON formatı: {example_json_str}"
            
            response = self.model.generate_content(prompt_text)
            print(f"Gemini API Response Object: {response}") # Log the entire response object
            if response.text:
                print(f"Gemini API Raw Response Text: {response.text}") # Log raw response text
                cleaned_response_text = response.text.strip()
                # Find the start and end of the JSON block
                json_start = cleaned_response_text.find('```json')
                json_end = cleaned_response_text.rfind('```')

                if json_start != -1 and json_end != -1 and json_start < json_end:
                    # Extract only the JSON part
                    json_string = cleaned_response_text[json_start + len('```json'):json_end].strip()
                else:
                    # If '```json' or '```' not found, try to parse the whole text (might be pure JSON)
                    json_string = cleaned_response_text
                
                print(f"Cleaned JSON string for parsing: {json_string[:500]}...") # Log cleaned JSON string
                try:
                    recommendations_data = json.loads(json_string)
                    print(f"Parsed recommendations data: {recommendations_data}") # Log parsed data
                    recommendations = []
                    for item in recommendations_data:
                        recommendations.append(RecommendationResult(
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            rating=item.get("rating", 0.0),
                            category=item.get("category", ""),
                            location=item.get("location", {})
                        ))
                    return recommendations
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error from Gemini API: {e}. Response text: {response.text[:200]}") # Log first 200 chars
                    return []
            else:
                print(f"Empty response text from Gemini API for query: {query}")
                return []
        except Exception as e:
            print(f"Error generating recommendations with Gemini API: {e}")
            return []

    def get_place_details(self, place_name: str) -> Optional[PlaceDetails]:
        try:
            prompt = f"""Bana '{place_name}' hakkında detaylı bilgi ver.
            Cevabı JSON formatında, adı (name), enlem (latitude), boylam (longitude), açıklama (description), kategori (category) ve puan (rating) içerecek şekilde ver.
            Eğer konum bilgisi mevcut değilse enlem ve boylam değerlerini null olarak bırakabilirsin.
            Örnek JSON formatı:
            {{"name": "Yer Adı", "latitude": 12.34, "longitude": 56.78, "description": "Detaylı Açıklama", "category": "Kategori", "rating": 4.5}}
            """
            response = self.model.generate_content(prompt)
            if response.text:
                cleaned_response_text = response.text.strip()
                # Find the start and end of the JSON block
                json_start = cleaned_response_text.find('```json')
                json_end = cleaned_response_text.rfind('```')

                if json_start != -1 and json_end != -1 and json_start < json_end:
                    # Extract only the JSON part
                    json_string = cleaned_response_text[json_start + len('```json'):json_end].strip()
                else:
                    # If '```json' or '```' not found, try to parse the whole text (might be pure JSON)
                    json_string = cleaned_response_text

                try:
                    place_data = json.loads(json_string)
                    return PlaceDetails(
                        name=place_data.get("name", place_name),
                        latitude=place_data.get("latitude"),
                        longitude=place_data.get("longitude"),
                        description=place_data.get("description", ""),
                        category=place_data.get("category", ""),
                        rating=place_data.get("rating", 0.0)
                    )
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error from Gemini API for place details: {e}. Response text: {response.text[:200]}")
                    return None
            return None
        except Exception as e:
            print(f"Error getting place details with Gemini API: {e}")
            return None
