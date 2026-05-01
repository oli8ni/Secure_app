import streamlit as st
import folium
import json
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Trajet Police", page_icon="🚔", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    .stApp > header {display: none !important;}
</style>
""", unsafe_allow_html=True)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.modules.geo import validate_coordinates, generate_route_points

st.markdown("""
<style>
    @keyframes pulse-dot {
        0% { r: 8; opacity: 0.8; }
        50% { r: 20; opacity: 0.2; }
        100% { r: 8; opacity: 0.8; }
    }
    .trajet-header {
        background: linear-gradient(90deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a1a 100%);
        border-bottom: 2px solid #1a1a4a;
        padding: 1rem 1.2rem;
        margin: -1rem -1rem 1rem -1rem;
    }
    .trajet-title {
        font-size: 1.5rem;
        font-weight: 900;
        color: #4B8BFF;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0;
    }
    .trajet-status {
        color: #00ff88;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    .info-panel {
        background: linear-gradient(145deg, #0d0d1a, #141428);
        border: 1px solid #1a1a3a;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #222;
        font-size: 0.9rem;
    }
    .info-label { color: #888; }
    .info-value { color: #fff; font-weight: bold; }
    .footer-co {
        text-align: center;
        color: #444;
        font-size: 0.75rem;
        margin-top: 2rem;
        padding: 1rem 0;
        border-top: 1px solid #1a1a1a;
    }
    .footer-co a { color: #4B8BFF; text-decoration: none; }
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #00ff88;
        border-radius: 50%;
        margin-right: 6px;
        animation: blink 1.5s infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)

# Get alert coords from session state
alert_lat = st.session_state.get('alert_lat', 0.0)
alert_lon = st.session_state.get('alert_lon', 0.0)
alert_id = st.session_state.get('alert_id', None)

if not validate_coordinates(alert_lat, alert_lon):
    st.error("Aucune alerte active trouvee. Envoyez d'abord une alerte.")
    if st.button("← RETOUR", key="back_no_alert"):
        st.switch_page("pages/client.py")
    st.stop()

# Police station coords (default Abidjan)
police_lat = 5.3600
police_lon = -4.0083

# Generate route
route_pts = generate_route_points(police_lat, police_lon, alert_lat, alert_lon, num_points=30)

st.markdown(f"""
<div class="trajet-header">
    <div class="trajet-title">🚔 SUIVI DU TRAJET POLICE</div>
    <div class="trajet-status"><span class="status-dot"></span>Alerte #{alert_id} - Police en route vers votre position</div>
</div>
""", unsafe_allow_html=True)

# Info panel
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<div class='info-panel'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#4B8BFF; margin-top:0;'>📍 Informations</h4>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="info-row"><span class="info-label">Votre position</span><span class="info-value">{alert_lat:.5f}, {alert_lon:.5f}</span></div>
    <div class="info-row"><span class="info-label">Poste police</span><span class="info-value">{police_lat:.5f}, {police_lon:.5f}</span></div>
    <div class="info-row"><span class="info-label">Statut</span><span class="info-value" style="color:#FF8800;">🟡 EN ROUTE</span></div>
    <div class="info-row"><span class="info-label">Heure</span><span class="info-value">{datetime.now().strftime('%H:%M:%S')}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("La police a ete notifiee de votre position et est en route. Restez a l'abri et gardez votre telephone allume.")
    
    if st.button("← RETOUR ALERTE", use_container_width=True):
        st.switch_page("pages/client.py")
    if st.button("🏠 RETOUR ACCUEIL", use_container_width=True):
        st.switch_page("streamlit_app.py")

with col2:
    # Map with route
    m = folium.Map(location=[(police_lat + alert_lat) / 2, (police_lon + alert_lon) / 2], zoom_start=13, tiles="CartoDB dark_matter")
    
    # Police station marker
    folium.Marker([police_lat, police_lon], icon=folium.Icon(color='blue', icon='building', prefix='fa'), popup="Poste de Police", tooltip="POLICE").add_to(m)
    
    # Victim position (pulsing circle)
    folium.CircleMarker([alert_lat, alert_lon], radius=25, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.3, popup="Votre position").add_to(m)
    folium.CircleMarker([alert_lat, alert_lon], radius=12, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.6, popup="Votre position").add_to(m)
    folium.Marker([alert_lat, alert_lon], icon=folium.Icon(color='red', icon='user', prefix='fa'), popup="Votre position", tooltip="VOUS").add_to(m)
    
    # Route polyline
    if route_pts:
        folium.PolyLine(route_pts, color='#FF8800', weight=5, opacity=0.9, popup="Trajet police").add_to(m)
        # Animated police car along route (midpoint)
        mid_idx = len(route_pts) // 3
        if mid_idx < len(route_pts):
            folium.Marker(route_pts[mid_idx], icon=folium.Icon(color='orange', icon='car', prefix='fa'), tooltip="🚔 POLICE EN ROUTE").add_to(m)
    
    st_folium(m, width=700, height=500, returned_objects=[])

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves
</div>
""", unsafe_allow_html=True)
