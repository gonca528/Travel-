import streamlit as st

def filters_component():
    st.markdown("--- (Filtreleme Seçenekleri) ---")
    selected_category = st.selectbox("Kategori Seçin", ["Tümü", "Müze", "Doğa", "Tarihi Yer"], key="filter_category")
    selected_features = st.multiselect("Ek Özellikler", ["Wifi", "Otopark", "Restoran"], key="filter_features")
    
    filters = {
        "category": selected_category,
        "features": selected_features
    }

    # if st.button("Filtreleri Uygula", key="apply_filters_button"):
    #     # This button can trigger a rerun of the app or update a session state variable
    #     # For now, filters are applied immediately when their values change
    #     pass

    return filters

