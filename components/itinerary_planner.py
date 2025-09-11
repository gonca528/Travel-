import streamlit as st
from typing import List, Dict, Any, Optional

def itinerary_planner_component(recommender):
    st.subheader("Gezi Planlayıcı")

    user_session_id = st.session_state.user_session_id
    
    # Mevcut gezi planlarını göster
    current_itineraries = recommender.db_manager.get_itineraries(user_session_id)

    if current_itineraries:
        st.write("**Mevcut Gezi Planlarınız:**")
        for it in current_itineraries:
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                st.write(f"- **{it['name']}** (Oluşturuldu: {it['created_at'].split(' ')[0]})")
            with col2:
                if st.button("Detaylar", key=f"show_itinerary_{it['id']}"):
                    st.session_state.selected_itinerary_id = it['id']
                    st.session_state.selected_itinerary_name = it['name']
            with col3:
                if st.button("Sil", key=f"delete_itinerary_{it['id']}"):
                    recommender.db_manager.delete_itinerary(it['id'])
                    st.success(f"Gezi planı '{it['name']}' silindi.")
                    st.experimental_rerun()

    # Yeni gezi planı oluştur
    with st.expander("Yeni Gezi Planı Oluştur/Mevcut Plana Ekle"):
        new_itinerary_name = st.text_input("Yeni gezi planı adı:", key="new_itinerary_name")
        if st.button("Plan Oluştur", key="create_new_itinerary_button"):
            if new_itinerary_name:
                itinerary_id = recommender.db_manager.create_itinerary(user_session_id, new_itinerary_name)
                if itinerary_id:
                    st.success(f"Gezi planı '{new_itinerary_name}' oluşturuldu!")
                    st.session_state.selected_itinerary_id = itinerary_id
                    st.session_state.selected_itinerary_name = new_itinerary_name
                    st.experimental_rerun()
                else:
                    st.error(f"Gezi planı '{new_itinerary_name}' zaten mevcut veya bir hata oluştu.")
            else:
                st.warning("Lütfen bir gezi planı adı girin.")

        # Seçili gezi planına yer ekle
        if 'selected_itinerary_id' in st.session_state and st.session_state.selected_itinerary_id:
            st.markdown(f"--- **'**{st.session_state.selected_itinerary_name}**' planına yer ekle --- ")
            available_places_for_itinerary = [rec.title for rec in st.session_state.latest_recommendations if rec.title not in [p['place_name'] for p in recommender.db_manager.get_itinerary_places(st.session_state.selected_itinerary_id)]]
            
            if available_places_for_itinerary:
                place_to_add = st.selectbox("Eklenecek yeri seçin:", available_places_for_itinerary, key="add_place_to_itinerary_select")
                if st.button(f"'{place_to_add}'i plana ekle", key=f"add_place_to_itinerary_button_{place_to_add}"):
                    # Mevcut yer sayısını alarak sırayı belirle
                    current_places = recommender.db_manager.get_itinerary_places(st.session_state.selected_itinerary_id)
                    order_index = len(current_places)
                    if recommender.db_manager.add_place_to_itinerary(st.session_state.selected_itinerary_id, place_to_add, order_index):
                        st.success(f"'{place_to_add}' plana eklendi!")
                        st.experimental_rerun()
                    else:
                        st.error(f"'{place_to_add}' plana eklenirken bir hata oluştu.")
            else:
                st.info("Eklenecek uygun yer bulunamadı (Tüm öneriler zaten planda olabilir veya yeni öneri yok).")

    # Seçili gezi planı detaylarını göster
    if 'selected_itinerary_id' in st.session_state and st.session_state.selected_itinerary_id:
        st.markdown(f"### Gezi Planı Detayları: {st.session_state.selected_itinerary_name}")
        itinerary_places = recommender.db_manager.get_itinerary_places(st.session_state.selected_itinerary_id)
        if itinerary_places:
            for place in itinerary_places:
                st.write(f"**{place['order_index'] + 1}. {place['place_name']}**")
                with st.expander(f"Detaylar ve Görseller - {place['place_name']}"):
                    st.write(f"**Açıklama:** {place.get('description', 'Mevcut değil.')}")
                    st.write(f"**Kategori:** {place.get('category', 'Mevcut değil.')}")
                    st.write(f"**Puan:** {place.get('rating', 'Mevcut değil.')} ⭐")
                    if place.get('latitude') is not None and place.get('longitude') is not None:
                        st.write(f"**Konum:** Lat: {place['latitude']}, Lng: {place['longitude']}")
                    else:
                        st.info("Konum bilgisi mevcut değil.")
                    
                    if place.get('image_urls'):
                        st.image(place['image_urls'], width=200, caption=[f"Photo {i+1}" for i in range(len(place['image_urls']))])
                    else:
                        st.info("Bu mekan için görsel bulunamadı.")

                    if st.button(f"Plandan Kaldır", key=f"remove_from_itinerary_{place['place_name']}_{st.session_state.selected_itinerary_id}"):
                        recommender.db_manager.remove_place_from_itinerary(st.session_state.selected_itinerary_id, place['place_name'])
                        st.success(f"'{place['place_name']}' plandan kaldırıldı.")
                        st.experimental_rerun()
        else:
            st.info("Bu gezi planında henüz yer bulunmamaktadır.")
