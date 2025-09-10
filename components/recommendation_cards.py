import streamlit as st
from services.gemini_service import RecommendationResult

def display_recommendation_card(recommendation: RecommendationResult):
    st.subheader(recommendation.title)
    st.write(f"**Kategori:** {recommendation.category}")
    st.write(f"**Puan:** {recommendation.rating} ⭐")
    
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
            st.experimental_rerun() # Favoriler listesini güncellemek için sayfayı yenile
    st.markdown("--- (Yeni Öneri Kartı) ---") # Kartlar arasında görsel ayırıcı
