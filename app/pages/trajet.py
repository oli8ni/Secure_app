import streamlit as st
import folium
import json
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Trajet Police", page_icon="🚔", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebarNav"]                 { display: none !important; }
    section[data-testid="stSidebar"]             { display: none !important; }
    button[kind="header"]                        { display: none !important; }
    .stApp > header                              { display: none !important; }
    div[data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
<script>
setTimeout(function(){
    var s = document.querySelector('section[data-testid="stSidebar"]');
    if (s) s.style.display = 'none';
    var n = document.querySelector('[data-testid="stSidebarNav"]');
    if (n) n.style.display = 'none';
    var c = document.querySelector('div[data-testid="stSidebarCollapsedControl"]');
    if (c) c.style.display = 'none';
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
    .th            { background:linear-gradient(90deg,#0a0a1a,#1a1a3a 50%,#0a0a1a); border-bottom:2px solid #1a1a4a; padding:1rem 1.2rem; margin:-1rem -1rem 1rem -1rem; }
    .tt            { font-size:1.5rem; font-weight:900; color:#4B8BFF; letter-spacing:3px; text-transform:uppercase; margin:0; }
    .ts-sub        { color:#0f8; font-size:.85rem; margin-top:.3rem; }
    .ip            { background:linear-gradient(145deg,#0d0d1a,#141428); border:1px solid #1a1a3a; border-radius:10px; padding:1rem; margin-bottom:1rem; }
    .ir            { display:flex; justify-content:space-between; padding:.5rem 0; border-bottom:1px solid #222; font-size:.9rem; }
    .il            { color:#888; }
    .iv            { color:#fff; font-weight:bold; }
    .footer-co     { text-align:center; color:#444; font-size:.75rem; margin-top:2rem; padding:1rem 0; border-top:1px solid #1a1a1a; }
    .footer-co a   { color:#4B8BFF; text-decoration:none; }
    .status-dot    { display:inline-block; width:10px; height:10px; background:#0f8; border-radius:50%; margin-right:6px; animation:blink 1.5s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
    .progress-bar  { background:#1a1a2e; border-radius:8px; height:20px; overflow:hidden; margin:1rem 0; }
    .progress-fill { background:linear-gradient(90deg,#4B8BFF,#0f8); height:100%; border-radius:8px; transition:width .5s; }
    .eta-box       { background:linear-gradient(145deg,#0d0d1a,#141428); border:1px solid #1a1a3a; border-radius:8px; padding:1rem; text-align:center; margin:1rem 0; }
    .eta-time      { font-size:2rem; font-weight:900; color:#4B8BFF; }
    .eta-label     { color:#666; font-size:.7rem; text-transform:uppercase; letter-spacing:2px; }
    .arrived-box   { background:linear-gradient(135deg,#0a2a0a,#1a3a1a); border:2px solid #0f4; border-radius:10px; padding:1.2rem; text-align:center; }
</style>
""", unsafe_allow_html=True)

# =========================
# LECTURE POSITION ALERTE
# ✅ FIX : fallback sur coordonnées de démo si la session est vide
#           (accès direct à la page, rechargement pendant la démo, etc.)
# =========================
DEMO_LAT = 5.3364  # Kinshasa — à adapter selon votre ville
DEMO_LON = 15.3222

alert_lat = st.session_state.get('alert_lat', 0.0)
alert_lon = st.session_state.get('alert_lon', 0.0)
alert_id  = st.session_state.get('alert_id', "DÉMO")

# Si les coordonnées sont nulles/invalides, on utilise le mode démo
is_demo = False
if not validate_coordinates(alert_lat, alert_lon):
    alert_lat = DEMO_LAT
    alert_lon = DEMO_LON
    alert_id  = "DÉMO"
    is_demo   = True

station     = get_default_station()
station_name = station['name'] if station is not None else "Poste Central"
police_lat  = station['latitude']  if station is not None else 5.3600
police_lon  = station['longitude'] if station is not None else 15.2960

# =========================
# PROGRESSION STABLE EN SESSION_STATE
# ✅ FIX : random.randint() à chaque render = position qui saute.
#           On stocke la valeur et on ne la recalcule qu'à l'init.
# =========================
if 'progress_pct' not in st.session_state:
    st.session_state.progress_pct = 10   # la police vient de partir
if 'eta_min' not in st.session_state:
    st.session_state.eta_min = 12

progress_pct = st.session_state.progress_pct
eta_min      = st.session_state.eta_min

# Calcul ETA dynamique en fonction de la progression
eta_min = max(1, int(12 * (1 - progress_pct / 100)))

# =========================
# ROUTE
# =========================
route_pts = generate_route_points(police_lat, police_lon, alert_lat, alert_lon, num_points=30)

# =========================
# HEADER
# =========================
st.markdown(f"""
<div class="th">
    <div class="tt">🚔 SUIVI DU TRAJET POLICE</div>
    <div class="ts-sub">
        <span class="status-dot"></span>Alerte #{alert_id} — Police en route
        {"&nbsp;&nbsp;<span style='color:#f80;font-size:.75rem'>⚠ Mode démonstration</span>" if is_demo else ""}
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# COLONNES : infos | carte
# =========================
col_info, col_map = st.columns([1, 2])

with col_info:
    # ETA
    if progress_pct >= 100:
        st.markdown("""
        <div class="arrived-box">
            <div style="font-size:2rem">🚔</div>
            <div style="color:#0f8;font-size:1.2rem;font-weight:bold">ARRIVÉE SUR PLACE</div>
            <div style="color:#888;font-size:.8rem">La police est à votre position</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="eta-box">
            <div class="eta-time">{eta_min}</div>
            <div class="eta-label">Minutes d'arrivée estimées</div>
        </div>
        """, unsafe_allow_html=True)

        # Barre de progression
        st.markdown(
            f"<div class='progress-bar'><div class='progress-fill' style='width:{progress_pct}%'></div></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='text-align:center;color:#888;font-size:.8rem'>Progression : {progress_pct}%</p>",
            unsafe_allow_html=True
        )

    # Infos alerte
    st.markdown(f"""
    <div class="ip">
        <h4 style="color:#4B8BFF;margin-top:0">📍 Informations</h4>
        <div class="ir"><span class="il">Votre position</span><span class="iv">{alert_lat:.5f}, {alert_lon:.5f}</span></div>
        <div class="ir"><span class="il">Poste police</span><span class="iv">{station_name}</span></div>
        <div class="ir"><span class="il">Position poste</span><span class="iv">{police_lat:.5f}, {police_lon:.5f}</span></div>
        <div class="ir"><span class="il">Progression</span><span class="iv" style="color:#FF8800">🟡 EN ROUTE — {progress_pct}%</span></div>
        <div class="ir"><span class="il">Heure</span><span class="iv">{datetime.now().strftime('%H:%M:%S')}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ✅ BOUTON SIMULATION : permet de montrer le déplacement en live lors de la démo
    st.markdown("<p style='color:#555;font-size:.75rem;text-align:center'>Simulation de progression</p>", unsafe_allow_html=True)
    sim1, sim2 = st.columns(2)
    with sim1:
        if st.button("▶ +10%", use_container_width=True, disabled=(progress_pct >= 100)):
            st.session_state.progress_pct = min(100, progress_pct + 10)
            st.rerun()
    with sim2:
        if st.button("↺ Reset", use_container_width=True):
            st.session_state.progress_pct = 10
            st.session_state.eta_min      = 12
            st.rerun()

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.info("La police est en route vers votre position. Restez à l'abri et gardez votre téléphone allumé.")

    if st.button("← RETOUR ALERTE",  use_container_width=True): st.switch_page("pages/client.py")
    if st.button("🏠 RETOUR ACCUEIL", use_container_width=True): st.switch_page("streamlit_app.py")

with col_map:
    center_lat = (police_lat + alert_lat) / 2
    center_lon = (police_lon + alert_lon) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )

    # Poste de police
    folium.Marker(
        [police_lat, police_lon],
        icon=folium.Icon(color='darkblue', icon='shield', prefix='fa'),
        tooltip=f"🚔 {station_name}"
    ).add_to(m)
    folium.Circle(
        [police_lat, police_lon], radius=300,
        fill=True, color='#4B8BFF', fill_color='#4B8BFF', fill_opacity=0.08
    ).add_to(m)

    # Victime
    folium.CircleMarker(
        [alert_lat, alert_lon], radius=15,
        fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.5,
        popup="Votre position"
    ).add_to(m)
    folium.Circle(
        [alert_lat, alert_lon], radius=120,
        fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.1
    ).add_to(m)
    folium.Marker(
        [alert_lat, alert_lon],
        icon=folium.Icon(color='red', icon='user', prefix='fa'),
        tooltip="👤 VOUS"
    ).add_to(m)

    if route_pts and len(route_pts) > 1:
        # Route complète (orange)
        folium.PolyLine(route_pts, color='#FF8800', weight=5, opacity=0.9).add_to(m)

        # Position actuelle de la police sur la route
        progress_idx = int(len(route_pts) * progress_pct / 100)
        progress_idx = min(progress_idx, len(route_pts) - 1)

        if progress_idx > 0:
            current_pos = route_pts[progress_idx]
            folium.Marker(
                current_pos,
                icon=folium.Icon(color='orange', icon='car', prefix='fa'),
                tooltip=f"🚔 POLICE — {progress_pct}%"
            ).add_to(m)
            folium.CircleMarker(
                current_pos, radius=10,
                fill=True, color='#FF8800', fill_color='#FF8800', fill_opacity=0.6
            ).add_to(m)

            # Partie déjà parcourue (vert)
            folium.PolyLine(
                route_pts[:progress_idx + 1],
                color='#00CC88', weight=4, opacity=0.9
            ).add_to(m)

    st_folium(m, width=700, height=530, returned_objects=[])

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&amp;O Itech Solution</a> | Tous droits réservés
</div>
""", unsafe_allow_html=True)
