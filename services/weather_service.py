from typing import List, Dict, Any, Optional, Tuple
import requests
from datetime import date

class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

    def geocode_city(self, city_name: str) -> Optional[Tuple[float, float]]:
        try:
            params = {
                "name": city_name,
                "count": 1,
                "language": "tr",
                "format": "json"
            }
            resp = requests.get(self.GEOCODING_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or []
            if not results:
                return None
            first = results[0]
            return (first.get("latitude"), first.get("longitude"))
        except Exception as e:
            print(f"Error geocoding city with Open-Meteo: {e}")
            return None

    def get_daily_forecast(self, latitude: float, longitude: float, start_date: date, end_date: date) -> Optional[List[Dict[str, Any]]]:
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "rain_sum",
                    "showers_sum",
                    "snowfall_sum",
                    "precipitation_probability_max",
                    "windspeed_10m_max"
                ],
                "timezone": "auto",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if not data or "daily" not in data:
                return None
            daily = data["daily"]
            days = []
            for idx, day in enumerate(daily.get("time", [])):
                days.append({
                    "date": day,
                    "temp_max": daily.get("temperature_2m_max", [None])[idx],
                    "temp_min": daily.get("temperature_2m_min", [None])[idx],
                    "precipitation_sum": daily.get("precipitation_sum", [None])[idx],
                    "rain_sum": daily.get("rain_sum", [None])[idx],
                    "showers_sum": daily.get("showers_sum", [None])[idx],
                    "snowfall_sum": daily.get("snowfall_sum", [None])[idx],
                    "precipitation_probability_max": daily.get("precipitation_probability_max", [None])[idx],
                    "windspeed_10m_max": daily.get("windspeed_10m_max", [None])[idx],
                })
            return days
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None

    @staticmethod
    def will_likely_rain(day: Dict[str, Any]) -> bool:
        prob = day.get("precipitation_probability_max")
        rain_sum = day.get("rain_sum")
        return (prob is not None and prob >= 50) or (rain_sum is not None and rain_sum >= 2.0)
