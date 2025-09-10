import streamlit as st

def search_component():
    st.subheader("Yeni Bir Gezi Planı Yapın")
    query = st.text_input("Nereye gitmek istersiniz veya ne tür bir gezi planlıyorsunuz?", key="main_search_input")
    
    # TODO: Add suggestion box for previous searches
    # TODO: Add category and filter options

    return query

