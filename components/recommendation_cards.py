import streamlit as st
import math
from typing import Optional, Tuple
from services.gemini_service import RecommendationResult
from services.popularity_service import PopularityService


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _distance_badge_html(dist_km: float) -> str:
    if dist_km <= 2:
        cls = "badge badge-green"
    elif dist_km <= 8:
        cls = "badge badge-amber"
    else:
        cls = "badge badge-red"
    return f"<span class='{cls}'>Merkeze uzaklık: {dist_km:.1f} km</span>"


def display_recommendation_card(recommendation: RecommendationResult, center_coords: Optional[Tuple[float, float]] = None):
    with st.container():
        st.markdown('<div class="recommendation-card">', unsafe_allow_html=True)
        st.markdown(f"<h3>{recommendation.title}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='category'><b>Kategori:</b> {recommendation.category}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rating'><b>Puan:</b> {recommendation.rating} ⭐</div>", unsafe_allow_html=True)

        # Suggested visit hours
        best, alt = PopularityService().suggest_hours(recommendation.category)
        st.markdown(f"<div class='category'><b>Önerilen ziyaret saati:</b> {best} <span style='color:#6b7280'>(Alternatif: {alt})</span></div>", unsafe_allow_html=True)

        # Distance from center (if available)
        if center_coords and recommendation.location and recommendation.location.get('lat') is not None and recommendation.location.get('lng') is not None:
            try:
                dist_km = _haversine_km(center_coords[0], center_coords[1], recommendation.location['lat'], recommendation.location['lng'])
                st.markdown(_distance_badge_html(dist_km), unsafe_allow_html=True)
            except Exception:
                pass

        with st.expander("Detayları Gör"):
            st.write(recommendation.description)
            if recommendation.location and recommendation.location.get('lat') is not None and recommendation.location.get('lng') is not None:
                st.write(f"**Konum:** Lat: {recommendation.location['lat']}, Lng: {recommendation.location['lng']}")
            else:
                st.info("Konum bilgisi mevcut değil.")
            
            if st.button(f"Favorilere Ekle", key=f"add_fav_{recommendation.title}"):
                if st.session_state.recommender.add_favorite(st.session_state.user_session_id, recommendation.title):
                    st.success(f"'{recommendation.title}' favorilere eklendi!")
                else:
                    st.error(f"'{recommendation.title}' favorilere eklenirken bir hata oluştu.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
