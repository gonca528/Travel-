import streamlit as st
import uuid
from services.recommendation_engine import RecommendationEngine, RecommendationResult
from components.recommendation_cards import display_recommendation_card
from components.map_component import map_component
from components.filters_component import filters_component
from services.email_service import EmailService
from services.weather_service import WeatherService
from datetime import date, timedelta

# 1. Ana Başlık ve Açıklama
st.set_page_config(
    page_title="Akıllı Gezi Rehberi",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize RecommendationEngine
if 'recommender' not in st.session_state:
    st.session_state.recommender = RecommendationEngine()

# Initialize EmailService
if 'email_service' not in st.session_state:
    try:
        st.session_state.email_service = EmailService()
    except ValueError as e:
        st.error(f"E-posta Servisi Hatası: {e}. Lütfen .env dosyanızdaki EMAIL_SENDER ve EMAIL_PASSWORD değerlerini kontrol edin.")
        st.session_state.email_service = None
    except Exception as e:
        st.error(f"E-posta Servisi başlatılırken bir hata oluştu: {e}")
        st.session_state.email_service = None

# Initialize WeatherService
if 'weather' not in st.session_state:
    st.session_state.weather = WeatherService()

# Initialize chat history, user session, and latest recommendations/route
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_session_id" not in st.session_state:
    st.session_state.user_session_id = str(uuid.uuid4())
if "latest_recommendations" not in st.session_state:
    st.session_state.latest_recommendations = []
if "latest_route" not in st.session_state:
    st.session_state.latest_route = None
if "selected_city" not in st.session_state:
    st.session_state.selected_city = ""

# --- Üst Başlık ve Sağ Üst Hava Durumu Widget'ı ---
left_col, right_col = st.columns([4, 1])
with left_col:
    st.title("🌍 Akıllı Gezi Rehberi")
    st.markdown("Seyahat planlarınızı yaparken size özel öneriler sunan akıllı rehberiniz.")
with right_col:
    st.markdown("<div class='weather-widget'>", unsafe_allow_html=True)
    st.markdown("<h3>Hava Bilgisi ☀️</h3>", unsafe_allow_html=True)
    dc1, dc2 = st.columns(2)
    with dc1:
        mini_start = st.date_input("Başlangıç", value=date.today(), key="mini_start", label_visibility="collapsed")
    with dc2:
        mini_end = st.date_input("Bitiş", value=date.today() + timedelta(days=2), key="mini_end", label_visibility="collapsed")
    city_for_weather = st.text_input("Şehir", value=st.session_state.selected_city, key="mini_city", placeholder="Şehir", label_visibility="collapsed")
    if st.button("Güncelle", key="mini_weather_btn") and city_for_weather.strip():
        coords = st.session_state.recommender.maps_service.get_place_coordinates(city_for_weather.strip())
        if not coords:
            fallback = st.session_state.weather.geocode_city(city_for_weather.strip())
            if fallback:
                class _Tmp:
                    def __init__(self, lat, lng):
                        self.latitude = lat
                        self.longitude = lng
                coords = _Tmp(fallback[0], fallback[1])
        if coords:
            forecast = st.session_state.weather.get_daily_forecast(coords.latitude, coords.longitude, mini_start, mini_end)
            if forecast:
                for day in forecast:
                    icon = "🌧️" if WeatherService.will_likely_rain(day) else "☀️"
                    temp_min = day.get('temp_min')
                    temp_max = day.get('temp_max')
                    st.markdown(f"<div class='weather-row'>{icon} {day['date']} | {temp_min}°C - {temp_max}°C</div>", unsafe_allow_html=True)
            else:
                st.info("Tahmin bulunamadı")
        else:
            st.info("Koordinat bulunamadı")
    st.markdown("</div>", unsafe_allow_html=True)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**Siz:** {message['content']}")
    elif message["role"] == "assistant":
        if message["type"] == "text":
            st.markdown(f"**Asistan:** {message['content']}")

# --- Yeni Tek Adımlı UI Akışı ---
with st.container():
    st.markdown("<div class=\"st-emotion-cache-k5i0t1\">", unsafe_allow_html=True)
    st.subheader("1. Seyahat Planınızı Yapın")
    
    selected_city_input = st.text_input("Seyahat etmek istediğiniz şehri girin:", key="city_input", value=st.session_state.selected_city)
    if selected_city_input != st.session_state.selected_city:
        st.session_state.selected_city = selected_city_input

    current_filters = filters_component()

    if st.button("Önerileri Getir", key="get_recommendations_button") and st.session_state.selected_city:
        with st.spinner("Harika öneriler arıyorum..."):
            try:
                full_query = f"{st.session_state.selected_city}"
                recommendations = st.session_state.recommender.get_travel_recommendations(
                    full_query, 
                    st.session_state.user_session_id,
                    filters=current_filters
                )
                st.session_state.latest_recommendations = recommendations
                if recommendations:
                    st.session_state.messages.append({"role": "assistant", "type": "recommendations", "content": recommendations})
                    st.markdown("**Asistan:** İşte size özel öneriler:")
                else:
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": "Üzgünüm, isteğinize uygun bir öneri bulamadım."})
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": "Lütfen farklı filtreler deneyin."})
                    st.markdown("**Asistan:** Üzgünüm, isteğinize uygun bir öneri bulamadım. Lütfen farklı filtreler deneyin.")
            except ValueError as e:
                st.error(f"API Anahtarı Hatası: {e}. Lütfen .env dosyanızı kontrol edin.")
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Öneriler ve Harita Bölümü ---
center_coords = None
if st.session_state.selected_city.strip():
    _coords = st.session_state.recommender.maps_service.get_place_coordinates(st.session_state.selected_city.strip())
    if not _coords:
        fb = st.session_state.weather.geocode_city(st.session_state.selected_city.strip())
        if fb:
            class _Tmp2:
                def __init__(self, lat, lng):
                    self.latitude = lat
                    self.longitude = lng
            _coords = _Tmp2(fb[0], fb[1])
    if _coords:
        center_coords = (_coords.latitude, _coords.longitude)

if st.session_state.latest_recommendations:
    st.markdown("<div class=\"st-emotion-cache-k5i0t1\">", unsafe_allow_html=True)
    st.subheader("Önerileriniz")
    for rec in st.session_state.latest_recommendations:
        display_recommendation_card(rec, center_coords=center_coords)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class=\"st-emotion-cache-k5i0t1\">", unsafe_allow_html=True)
    st.subheader("Harita")
    map_component(st.session_state.latest_recommendations, st.session_state.latest_route)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Henüz bir öneri bulunmamaktadır. Lütfen yukarıdaki formu doldurarak arama yapın.")

# --- Favoriler Bölümü ---
st.markdown("<div class=\"st-emotion-cache-k5i0t1\">", unsafe_allow_html=True)
st.subheader("Favorilerim")
favorites = st.session_state.recommender.get_favorites(st.session_state.user_session_id)
if favorites:
    st.markdown("<div class='chips'>", unsafe_allow_html=True)
    for fav_place in favorites:
        st.markdown(f"<span class='chip'>{fav_place}</span>", unsafe_allow_html=True)
        if st.button(f"Favorilerden Çıkar", key=f"remove_fav_{fav_place}"):
            st.session_state.recommender.remove_favorite(st.session_state.user_session_id, fav_place)
            st.success(f"'{fav_place}' favorilerden çıkarıldı.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Henüz favori bir yeriniz bulunmamaktadır.")

# Favorileri E-posta Gönder Bölümü (Aktif)
if favorites and st.session_state.get('email_service'):
    st.subheader("Favorileri E-posta Olarak Gönder")
    recipient_email = st.text_input("E-posta adresinizi girin:", key="email_input")
    if st.button("Favorileri Gönder", key="send_favorites_email_button"):
        if recipient_email:
            with st.spinner("Favorileriniz e-posta ile gönderiliyor..."):
                favorite_trip_details = st.session_state.recommender.db_manager.get_favorite_place_details(st.session_state.user_session_id)
                if st.session_state.email_service.send_favorite_trips_email(recipient_email, favorite_trip_details):
                    st.success(f"Favori gezileriniz {recipient_email} adresine başarıyla gönderildi!")
                else:
                    st.error("E-posta gönderilirken bir hata oluştu. Lütfen bilgilerinizi kontrol edin.")
        else:
            st.warning("Lütfen e-posta adresinizi girin.")
