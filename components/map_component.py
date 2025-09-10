import streamlit as st
from streamlit_folium import folium_static
import folium
from services.gemini_service import RecommendationResult
from services.maps_service import RouteInfo, Coordinates
from typing import List, Optional

def map_component(recommendations: List[RecommendationResult] = None, route: Optional[RouteInfo] = None):
    # Default center if no recommendations
    start_coords = [39.9334, 32.8597]  # Ankara, Turkey as default
    if recommendations and recommendations[0].location:
        start_coords = [recommendations[0].location['lat'], recommendations[0].location['lng']]

    m = folium.Map(location=start_coords, zoom_start=10)

    # Add markers for recommendations
    if recommendations:
        for rec in recommendations:
            if rec.location and rec.location.get('lat') is not None and rec.location.get('lng') is not None:
                folium.Marker(
                    [rec.location['lat'], rec.location['lng']],
                    popup=f"<b>{rec.title}</b><br>{rec.description}<br>Puan: {rec.rating}",
                    tooltip=rec.title
                ).add_to(m)

    # Add route to map if available
    if route:
        # TODO: Implement drawing the route on the map using route.steps or polylines
        st.info(f"Rota: {route.distance}, Süre: {route.duration}")
        st.markdown("**Rota Adımları:**")
        for step in route.steps:
            st.markdown(f"- {step}")

    # Display the map
    folium_static(m, width=700, height=500)

