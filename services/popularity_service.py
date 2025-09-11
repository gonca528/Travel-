from typing import Dict, Tuple

class PopularityService:
    """Heuristic visit time suggestions by category. Returns (best_time, alternative_time)."""
    CATEGORY_RULES: Dict[str, Tuple[str, str]] = {
        "Müze": ("10:00-12:00", "15:00-17:00"),
        "Tarihi Yer": ("09:00-11:00", "16:00-18:00"),
        "Park": ("08:00-10:00", "17:00-19:00"),
        "Plaj": ("09:00-11:00", "16:00-19:00"),
        "Alışveriş": ("11:00-13:00", "18:00-20:00"),
        "Kafe": ("10:00-12:00", "16:00-18:00"),
        "Restoran": ("12:00-14:00", "19:00-21:00"),
        "Doğa": ("08:00-10:00", "16:00-18:00"),
    }

    DEFAULT: Tuple[str, str] = ("10:00-12:00", "16:00-18:00")

    def suggest_hours(self, category: str) -> Tuple[str, str]:
        for key, val in self.CATEGORY_RULES.items():
            if key.lower() in (category or "").lower():
                return val
        return self.DEFAULT

