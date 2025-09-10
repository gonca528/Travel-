import streamlit as st
import uuid
from services.recommendation_engine import RecommendationEngine, RecommendationResult
from components.recommendation_cards import display_recommendation_card
from components.map_component import map_component
from components.filters_component import filters_component
# from components.city_selection_component import city_selection_component # Kaldırıldı

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

# Initialize chat history, user session, and latest recommendations/route
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_session_id" not in st.session_state:
    st.session_state.user_session_id = str(uuid.uuid4())
if "latest_recommendations" not in st.session_state:
    st.session_state.latest_recommendations = []
if "latest_route" not in st.session_state:
    st.session_state.latest_route = None
# if "current_step" not in st.session_state: # Kaldırıldı
#     st.session_state.current_step = "city_selection"
if "selected_city" not in st.session_state:
    st.session_state.selected_city = ""

st.title("🌍 Akıllı Gezi Rehberi")
st.markdown("Seyahat planlarınızı yaparken size özel öneriler sunan akıllı rehberiniz.")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**Siz:** {message['content']}")
    elif message["role"] == "assistant":
        if message["type"] == "text":
            st.markdown(f"**Asistan:** {message['content']}")
        # Removed recommendation cards from chat history to avoid DuplicateWidgetID

# --- Yeni Tek Adımlı UI Akışı ---
with st.container():
    st.markdown("<div class=\"st-emotion-cache-k5i0t1\">", unsafe_allow_html=True)
    st.subheader("1. Seyahat Planınızı Yapın")
    
    selected_city_input = st.text_input("Seyahat etmek istediğiniz şehri girin:", key="city_input", value=st.session_state.selected_city)
    if selected_city_input != st.session_state.selected_city:
        st.session_state.selected_city = selected_city_input
        # st.experimental_rerun() # Otomatik getirme yapıldığı için gerek kalmadı

    current_filters = filters_component() # Call the filters component and get selected values

    if st.button("Önerileri Getir", key="get_recommendations_button") and st.session_state.selected_city:
        # st.session_state.messages.append({"role": "user", "type": "text", "content": f"Şehir: {st.session_state.selected_city}, Filtreler: {current_filters}"}) # Kaldırıldı
        # st.markdown(f"**Siz:** Şehir: {st.session_state.selected_city}, Filtreler: {current_filters}") # Kaldırıldı

        with st.spinner("Harika öneriler arıyorum..."):
            try:
                full_query = f"{st.session_state.selected_city}"
                recommendations = st.session_state.recommender.get_travel_recommendations(
                    full_query, 
                    st.session_state.user_session_id,
                    filters=current_filters # Pass filters here
                )
                st.session_state.latest_recommendations = recommendations # Update latest recommendations
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
if st.session_state.latest_recommendations:
    st.markdown("<div class=\"st-emotion-cache-k5i0t1\">", unsafe_allow_html=True)
    st.subheader("Önerileriniz")
    for rec in st.session_state.latest_recommendations:
        display_recommendation_card(rec)
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
    for fav_place in favorites:
        st.write(f"- {fav_place}")
        if st.button(f"Favorilerden Çıkar", key=f"remove_fav_{fav_place}"):
            st.session_state.recommender.remove_favorite(st.session_state.user_session_id, fav_place)
            st.success(f"'{fav_place}' favorilerden çıkarıldı.")
            st.experimental_rerun()
else:
    st.info("Henüz favori bir yeriniz bulunmamaktadır.")
st.markdown("</div>", unsafe_allow_html=True)
