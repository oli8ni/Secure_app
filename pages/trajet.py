import streamlit as st
import folium
import json
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Trajet Police", page_icon="🚔", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebarNav"]{display:none!important}
    section[data-testid="stSidebar"]{display:none!important}
    button[kind="header"]{display:none!important}
    .stApp>header{display:none!important}
    div[data-testid="stSidebarCollapsedControl"]{display:none!important}
</style>
<script>
setTimeout(function(){
    var s=document.querySelector('section[data-testid="stSidebar"]');
    if(s)s.style.display='none';
    var n=document.querySelector('[data-testid="stSidebarNav"]');
    if(n)n.style.display='none';
    var c=document.querySelector('div[data-testid="stSidebarCollapsedControl"]');
    if(c)c.style.display='none';
}, 500);
</script>
""", unsafe_allow_html=True)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.modules.database import init_db, get_default_station
from app.modules.geo import validate_coordinates, generate_route_points
from streamlit_folium import st_folium

init_db()

st.markdown("""
<style>
    .th{background:linear-gradient(90deg,#0a0a1a,#1a1a3a 50%,#0a0a1a);border-bottom:2px solid #1a1a4a;padding:1rem 1.2rem;margin:-1rem -1rem 1rem -1rem}
    .tt{font-size:1.5rem;font-weight:900;color:#4B8BFF;letter-spacing:3px;text-transform:uppercase;margin:0}
    .ts{color:#0f8;font-size:.85rem;margin-top:.3rem}
    .ip{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #1a1a3a;border-radius:10px;padding:1rem;margin-bottom:1rem}
    .ir{display:flex;justify-content:space-between;padding:.5rem 0;border-bottom:1px solid #222;font-size:.9rem}
    .il{color:#888}.iv{color:#fff;font-weight:bold}
    .footer-co{text-align:center;color:#444;font-size:.75rem;margin-top:2rem;padding:1rem 0;border-top:1px solid #1a1a1a}
    .footer-co a{color:#4B8BFF;text-decoration:none}
    .status-dot{display:inline-block;width:10px;height:10px;background:#0f8;border-radius:50%;margin-right:6px;animation:blink 1.5s infinite}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
    .progress-bar{background:#1a1a2e;border-radius:8px;height:20px;overflow:hidden;margin:1rem 0}
    .progress-fill{background:linear-gradient(90deg,#4B8BFF,#0f8);height:100%;border-radius:8px;transition:width .5s}
    .eta-box{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #1a1a3a;border-radius:8px;padding:1rem;text-align:center;margin:1rem 0}
    .eta-time{font-size:2rem;font-weight:900;color:#4B8BFF}
    .eta-label{color:#666;font-size:.7rem;text-transform:uppercase;letter-spacing:2px}
</style>
""", unsafe_allow_html=True)

alert_lat = st.session_state.get('alert_lat', 0.0)
alert_lon = st.session_state.get('alert_lon', 0.0)
alert_id = st.session_state.get('alert_id', None)

if not validate_coordinates(alert_lat, alert_lon):
    st.error("Aucune alerte active. Envoyez d'abord une alerte.")
    if st.button("← RETOUR"): st.switch_page("pages/client.py")
    st.stop()

station = get_default_station()
station_name = station['name'] if station is not None else "Police"
police_lat = station['latitude'] if station is not None else 5.36
police_lon = station['longitude'] if station is not None else -4.0083

route_pts = generate_route_points(police_lat, police_lon, alert_lat, alert_lon, num_points=30)

# Simuler progression (comme Yango)
import random
progress_pct = random.randint(25, 75)
eta_min = random.randint(3, 12)

st.markdown(f"""
<div class="th">
    <div class="tt">🚔 SUIVI DU TRAJET POLICE</div>
    <div class="ts"><span class="status-dot"></span>Alerte #{alert_id} - Police en route</div>
</div>""", unsafe_allow_html=True)

# Progression style Yango
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<div class='eta-box'>", unsafe_allow_html=True)
    st.markdown(f'<div class="eta-time">{eta_min}</div>', unsafe_allow_html=True)
    st.markdown('<div class="eta-label">Minutes d\'arrivee estimees</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='progress-bar'><div class='progress-fill' style='width:" + str(progress_pct) + "%'></div></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:#888;font-size:.8rem'>Progression : {progress_pct}%</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='ip'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#4B8BFF;margin-top:0'>📍 Informations</h4>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ir"><span class="il">Votre position</span><span class="iv">{alert_lat:.5f}, {alert_lon:.5f}</span></div>
    <div class="ir"><span class="il">Poste police</span><span class="iv">{station_name}</span></div>
    <div class="ir"><span class="il">Position police</span><span class="iv">{police_lat:.5f}, {police_lon:.5f}</span></div>
    <div class="ir"><span class="il">Statut</span><span class="iv" style="color:#FF8800">🟡 EN ROUTE</span></div>
    <div class="ir"><span class="il">Heure</span><span class="iv">{datetime.now().strftime('%H:%M:%S')}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("La police est en route vers votre position. Restez a l'abri et gardez votre telephone allume.")
    if st.button("← RETOUR ALERTE", use_container_width=True): st.switch_page("pages/client.py")
    if st.button("🏠 RETOUR ACCUEIL", use_container_width=True): st.switch_page("streamlit_app.py")

with col2:
    m = folium.Map(location=[(police_lat + alert_lat)/2, (police_lon + alert_lon)/2], zoom_start=13, tiles="CartoDB dark_matter")
    
    # Poste de police
    folium.Marker([police_lat, police_lon], icon=folium.Icon(color='darkblue', icon='shield', prefix='fa'), tooltip=f"🚔 {station_name}").add_to(m)
    folium.Circle([police_lat, police_lon], radius=300, fill=True, color='#4B8BFF', fill_color='#4B8BFF', fill_opacity=0.08).add_to(m)
    
    # Victime (pulsing red)
    folium.CircleMarker([alert_lat, alert_lon], radius=15, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.5, popup="Votre position").add_to(m)
    folium.Circle([alert_lat, alert_lon], radius=120, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.1).add_to(m)
    folium.Marker([alert_lat, alert_lon], icon=folium.Icon(color='red', icon='user', prefix='fa'), tooltip="👤 VOUS").add_to(m)
    
    # Route complete
    if route_pts:
        folium.PolyLine(route_pts, color='#FF8800', weight=5, opacity=0.9).add_to(m)
        
        # Position actuelle de la police (progression sur la route)
        progress_idx = int(len(route_pts) * progress_pct / 100)
        if progress_idx >= len(route_pts): progress_idx = len(route_pts) - 1
        if progress_idx > 0:
            current_pos = route_pts[progress_idx]
            folium.Marker(current_pos, icon=folium.Icon(color='orange', icon='car', prefix='fa'), tooltip=f"🚔 POLICE - {progress_pct}%").add_to(m)
            folium.CircleMarker(current_pos, radius=10, fill=True, color='#FF8800', fill_color='#FF8800', fill_opacity=0.6).add_to(m)
        
        # Partie parcourue (vert) vs restante (orange)
        if progress_idx > 1:
            folium.PolyLine(route_pts[:progress_idx+1], color='#00CC88', weight=4, opacity=0.9).add_to(m)
    
    st_folium(m, width=700, height=520, returned_objects=[])

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves
</div>""", unsafe_allow_html=True)
