from dotenv import load_dotenv
import os


def _get_secret(key: str):
    try:
        import streamlit as st
        try:
            # Direct access; if secrets are not configured, this will raise and we return None
            return st.secrets[key]
        except Exception:
            return None
    except Exception:
        return None

load_dotenv()

GEMINI_API_KEY = _get_secret("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = _get_secret("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

