import sqlite3
import json
from typing import Optional, Dict, Any, List

DB_PATH = 'database/travel_recommendations.db'

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._create_tables()
        self._migrate_schema()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query TEXT NOT NULL,
                    search_results JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_session_id TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS places_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_name TEXT NOT NULL,
                    latitude REAL NULL,  -- NULL kabul edilecek şekilde değiştirildi
                    longitude REAL NULL, -- NULL kabul edilecek şekilde değiştirildi
                    description TEXT,
                    category TEXT,
                    rating REAL,
                    image_urls JSON NULL,  -- Yeni eklendi
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_session_id TEXT,
                    place_name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itineraries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_session_id, name)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itinerary_places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itinerary_id INTEGER NOT NULL,
                    place_name TEXT NOT NULL,
                    order_index INTEGER NOT NULL,
                    FOREIGN KEY (itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE,
                    UNIQUE(itinerary_id, order_index),
                    UNIQUE(itinerary_id, place_name)
                );
            """)
            conn.commit()

    def _migrate_schema(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Ensure image_urls column exists on places_cache
                cursor.execute("PRAGMA table_info(places_cache);")
                existing_columns = [row[1] for row in cursor.fetchall()]
                if "image_urls" not in existing_columns:
                    cursor.execute("ALTER TABLE places_cache ADD COLUMN image_urls JSON NULL;")
                    conn.commit()
        except Exception as e:
            print(f"Schema migration error: {e}")

    def save_search_result(self, query: str, results: Dict[str, Any], user_session_id: Optional[str] = None) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO search_history (search_query, search_results, user_session_id)
                    VALUES (?, ?, ?);
                """, (query, json.dumps(results), user_session_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving search result: {e}")
            return False

    def get_cached_results(self, query: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT search_results FROM search_history WHERE search_query = ? ORDER BY created_at DESC LIMIT 1;", (query,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
            
    def save_place_to_cache(self, place_name: str, latitude: Optional[float], longitude: Optional[float], description: str, category: str, rating: float, image_urls: Optional[List[str]] = None) -> bool:
        try:
            print(f"DEBUG: save_place_to_cache called for: {place_name}") # DEBUG
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO places_cache (place_name, latitude, longitude, description, category, rating, image_urls)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (place_name, latitude, longitude, description, category, rating, json.dumps(image_urls) if image_urls else None))
                conn.commit()
            print(f"DEBUG: Successfully saved {place_name} to cache.") # DEBUG
            return True
        except Exception as e:
            print(f"Error saving place to cache: {e}")
            return False

    def get_cached_place_details(self, place_name: str) -> Optional[Dict[str, Any]]:
        print(f"DEBUG: get_cached_place_details called for: {place_name}") # DEBUG
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT latitude, longitude, description, category, rating, image_urls FROM places_cache WHERE place_name = ? ORDER BY cached_at DESC LIMIT 1;", (place_name,))
            row = cursor.fetchone()
            if row:
                details = {
                    "latitude": row[0],
                    "longitude": row[1],
                    "description": row[2],
                    "category": row[3],
                    "rating": row[4],
                    "image_urls": json.loads(row[5]) if row[5] else [] # Yeni eklendi
                }
                print(f"DEBUG: Found cached details for {place_name}: {details}") # DEBUG
                return details
            print(f"DEBUG: No cached details found for {place_name}.") # DEBUG
            return None

    def add_to_favorites(self, user_session_id: str, place_name: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_favorites (user_session_id, place_name)
                    VALUES (?, ?);
                """, (user_session_id, place_name))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding to favorites: {e}")
            return False

    def get_favorites(self, user_session_id: str) -> List[str]:
        print(f"DEBUG: get_favorites called for session: {user_session_id}") # DEBUG
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT place_name FROM user_favorites WHERE user_session_id = ?;", (user_session_id,))
            favorites = [row[0] for row in cursor.fetchall()]
            print(f"DEBUG: Retrieved favorites for session {user_session_id}: {favorites}") # DEBUG
            return favorites

    def get_favorite_place_details(self, user_session_id: str) -> List[Dict[str, Any]]:
        print(f"DEBUG: get_favorite_place_details called for session: {user_session_id}") # DEBUG
        favorite_place_names = self.get_favorites(user_session_id)
        favorite_places_details = []
        for place_name in favorite_place_names:
            details = self.get_cached_place_details(place_name)
            if details:
                details["place_name"] = place_name  # Add place_name to the details
                favorite_places_details.append(details)
            else:
                # Fall back to minimal info so emails are not empty
                favorite_places_details.append({
                    "place_name": place_name,
                    "description": None,
                    "category": None,
                    "rating": None,
                    "image_urls": []
                })
        print(f"DEBUG: Final favorite place details for email: {favorite_places_details}") # DEBUG
        return favorite_places_details

    def remove_from_favorites(self, user_session_id: str, place_name: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_favorites WHERE user_session_id = ? AND place_name = ?;", (user_session_id, place_name))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error removing from favorites: {e}")
            return False

    def create_itinerary(self, user_session_id: str, name: str) -> Optional[int]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO itineraries (user_session_id, name) VALUES (?, ?);", (user_session_id, name))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Itinerary with name '{name}' already exists for session {user_session_id}.")
            return None
        except Exception as e:
            print(f"Error creating itinerary: {e}")
            return None

    def add_place_to_itinerary(self, itinerary_id: int, place_name: str, order_index: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO itinerary_places (itinerary_id, place_name, order_index) VALUES (?, ?, ?);", (itinerary_id, place_name, order_index))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            print(f"Place '{place_name}' already in itinerary {itinerary_id} or order index {order_index} is taken.")
            return False
        except Exception as e:
            print(f"Error adding place to itinerary: {e}")
            return False

    def get_itineraries(self, user_session_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM itineraries WHERE user_session_id = ? ORDER BY created_at DESC;", (user_session_id,))
            return [{"id": row[0], "name": row[1], "created_at": row[2]} for row in cursor.fetchall()]

    def get_itinerary_places(self, itinerary_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # places_cache tablosundan detayları almak için JOIN kullanıldı
            cursor.execute("""
                SELECT ip.place_name, ip.order_index,
                       pc.latitude, pc.longitude, pc.description, pc.category, pc.rating, pc.image_urls
                FROM itinerary_places ip
                LEFT JOIN places_cache pc ON ip.place_name = pc.place_name
                WHERE ip.itinerary_id = ?
                ORDER BY ip.order_index;
            """, (itinerary_id,))
            
            results = []
            for row in cursor.fetchall():
                place_details = {
                    "place_name": row[0],
                    "order_index": row[1],
                    "latitude": row[2],
                    "longitude": row[3],
                    "description": row[4],
                    "category": row[5],
                    "rating": row[6],
                    "image_urls": json.loads(row[7]) if row[7] else []
                }
                results.append(place_details)
            return results

    def remove_place_from_itinerary(self, itinerary_id: int, place_name: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM itinerary_places WHERE itinerary_id = ? AND place_name = ?;", (itinerary_id, place_name))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error removing place from itinerary: {e}")
            return False

    def delete_itinerary(self, itinerary_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM itineraries WHERE id = ?;", (itinerary_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting itinerary: {e}")
            return False

