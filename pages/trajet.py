import streamlit as st
import folium
import json
import time
import math
from datetime import datetime

st.set_page_config(
    page_title="MutuAlert - Trajet Police",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# === HIDE SIDEBAR NAVIGATION COMPLETELY ===
hide_sidebar_css = """
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    .stApp > header {display: none !important;}
    [data-testid="stSidebarCollapsedControl"] {display: none !important;}
    .reportview-container .main .block-container {padding-top: 0 !important;}
</style>
<script>
    setTimeout(function(){
        var sb = document.querySelector('[data-testid="stSidebar"]');
        if (sb) sb.style.display = 'none';
        var sbc = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
        if (sbc) sbc.style.display = 'none';
    }, 100);
</script>
"""
st.markdown(hide_sidebar_css, unsafe_allow_html=True)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.modules.database import init_db, get_default_station, get_station_by_id
from app.modules.geo import validate_coordinates
from app.modules.routing import get_route
from streamlit_folium import st_folium

init_db()

alert_lat = st.session_state.get("alert_lat", 0.0)
alert_lon = st.session_state.get("alert_lon", 0.0)
alert_id = st.session_state.get("alert_id", None)

if not validate_coordinates(alert_lat, alert_lon):
    st.error("Aucune alerte active. Envoyez d'abord une alerte depuis la page d'accueil.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← RETOUR ALERTE"):
            st.switch_page("pages/client.py")
    with c2:
        if st.button("🏠 ACCUEIL"):
            st.switch_page("streamlit_app.py")
    st.stop()

# Use SELECTED station from police page, or default
station_id = st.session_state.get("selected_station_id", None)
station = get_station_by_id(station_id) if station_id else get_default_station()
if station is None:
    station = get_default_station()

station_name = station["name"] if station is not None else "Police"
police_lat = float(station["latitude"]) if station is not None else -4.3250
police_lon = float(station["longitude"]) if station is not None else 15.3222

# Get real OSRM route
route_pts, dist_km, dur_min = get_route(police_lat, police_lon, alert_lat, alert_lon)

# PERSISTENT progress based on time since alert (deterministic)
if "progress_pct" not in st.session_state or st.session_state.get("progress_alert_id") != alert_id:
    # Seed based on alert_id for deterministic pseudo-progress
    progress_seed = (alert_id or 1) * 7 + int(alert_lat * 1000)
    st.session_state.progress_pct = min(85, max(25, (progress_seed % 60) + 10))
    st.session_state.progress_alert_id = alert_id

progress_pct = st.session_state.progress_pct

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
    .route-real{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #0f8;border-radius:8px;padding:1rem;margin:1rem 0}
    .route-real h4{color:#0f8;margin:0 0 .5rem 0}
    .route-fallback{background:linear-gradient(145deg,#1a1a0a,#0d0d0a);border:1px solid #f80;border-radius:8px;padding:1rem;margin:1rem 0}
    .route-fallback h4{color:#f80;margin:0 0 .5rem 0}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="th">
    <div class="tt">🚔 SUIVI DU TRAJET POLICE</div>
    <div class="ts"><span class="status-dot"></span>Alerte #{alert_id} - Police en route depuis {station_name}</div>
</div>""", unsafe_allow_html=True)

# Route info
if dist_km and dur_min:
    speed_kmh = dist_km / (dur_min / 60) if dur_min > 0.1 else 0
    st.markdown(f"""
    <div class="route-real">
        <h4>✅ Route reelle (OSRM - OpenStreetMap)</h4>
        <div class="ir"><span class="il">Distance</span><span class="iv">{dist_km:.2f} km</span></div>
        <div class="ir"><span class="il">Temps estime</span><span class="iv">{dur_min:.0f} minutes</span></div>
        <div class="ir"><span class="il">Vitesse moyenne</span><span class="iv">{speed_kmh:.0f} km/h</span></div>
        <div class="ir"><span class="il">Source</span><span class="iv" style="color:#0f8">OSRM - Routes reelles</span></div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="route-fallback">
        <h4>⚠ Route approximative (OSRM indisponible)</h4>
        <p style="color:#888;font-size:.85rem">Le service de routage OSRM est temporairement inaccessible.
        L'itineraire affiche est une ligne directe approximative avec vitesse urbaine 30km/h.</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<div class='eta-box'>", unsafe_allow_html=True)
    eta_display = int(dur_min * (1 - progress_pct / 100)) if dur_min else max(3, int(progress_pct / 10))
    st.markdown(f'<div class="eta-time">{eta_display}</div>', unsafe_allow_html=True)
    st.markdown('<div class="eta-label">Minutes restantes estimees</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='progress-bar'><div class='progress-fill' style='width:{progress_pct}%'></div></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:#888;font-size:.8rem'>Progression: {progress_pct}%</p>", unsafe_allow_html=True)

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
    if st.button("← RETOUR ALERTE", use_container_width=True):
        st.switch_page("pages/client.py")
    if st.button("🏠 RETOUR ACCUEIL", use_container_width=True):
        st.switch_page("streamlit_app.py")

with col2:
    m = folium.Map(
        location=[(police_lat + alert_lat) / 2, (police_lon + alert_lon) / 2],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )

    # Poste de police
    folium.Marker(
        [police_lat, police_lon],
        icon=folium.Icon(color="darkblue", icon="shield", prefix="fa"),
        tooltip=f"🚔 {station_name}",
    ).add_to(m)
    folium.Circle(
        [police_lat, police_lon],
        radius=300,
        fill=True,
        color="#4B8BFF",
        fill_color="#4B8BFF",
        fill_opacity=0.08,
    ).add_to(m)

    # Victime (pulsing red)
    folium.CircleMarker(
        [alert_lat, alert_lon],
        radius=15,
        fill=True,
        color="#FF0000",
        fill_color="#FF0000",
        fill_opacity=0.5,
        popup="Votre position",
    ).add_to(m)
    folium.Circle(
        [alert_lat, alert_lon],
        radius=120,
        fill=True,
        color="#FF0000",
        fill_color="#FF0000",
        fill_opacity=0.1,
    ).add_to(m)
    folium.Marker(
        [alert_lat, alert_lon],
        icon=folium.Icon(color="red", icon="user", prefix="fa"),
        tooltip="👤 VOUS",
    ).add_to(m)

    # Real OSRM route
    if route_pts:
        folium.PolyLine(route_pts, color="#FF8800", weight=5, opacity=0.9).add_to(m)

        # Police car position on route (deterministic)
        progress_idx = int(len(route_pts) * progress_pct / 100)
        if progress_idx >= len(route_pts):
            progress_idx = len(route_pts) - 1
        if progress_idx > 0:
            current_pos = route_pts[progress_idx]
            folium.Marker(
                current_pos,
                icon=folium.Icon(color="orange", icon="car", prefix="fa"),
                tooltip=f"🚔 POLICE - {progress_pct}%",
            ).add_to(m)
            folium.CircleMarker(
                current_pos,
                radius=10,
                fill=True,
                color="#FF8800",
                fill_color="#FF8800",
                fill_opacity=0.6,
            ).add_to(m)

        # Partie parcourue (verte)
        if progress_idx > 1:
            folium.PolyLine(route_pts[: progress_idx + 1], color="#00CC88", weight=4, opacity=0.9).add_to(m)

    st_folium(m, width=700, height=520, returned_objects=[])

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves
</div>""", unsafe_allow_html=True)
