import sqlite3
import json
from typing import Optional, Dict, Any, List

DB_PATH = 'database/travel_recommendations.db'

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._create_tables()

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
                    latitude REAL,
                    longitude REAL,
                    description TEXT,
                    category TEXT,
                    rating REAL,
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
            conn.commit()

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
            
    def save_place_to_cache(self, place_name: str, latitude: float, longitude: float, description: str, category: str, rating: float) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO places_cache (place_name, latitude, longitude, description, category, rating)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (place_name, latitude, longitude, description, category, rating))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving place to cache: {e}")
            return False

    def get_cached_place_details(self, place_name: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT latitude, longitude, description, category, rating FROM places_cache WHERE place_name = ? ORDER BY cached_at DESC LIMIT 1;", (place_name,))
            row = cursor.fetchone()
            if row:
                return {
                    "latitude": row[0],
                    "longitude": row[1],
                    "description": row[2],
                    "category": row[3],
                    "rating": row[4],
                }
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT place_name FROM user_favorites WHERE user_session_id = ?;", (user_session_id,))
            return [row[0] for row in cursor.fetchall()]

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

