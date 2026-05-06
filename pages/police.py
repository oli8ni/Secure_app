import streamlit as st
import folium
import json
import time
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="MutuAlert - Centre de Commandement",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="collapsed"
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
from app.modules.database import (
    init_db, get_all_alerts, update_alert_status, add_route_data,
    get_police_stations, get_default_station, get_station_by_id,
    add_police_station, update_station_default, delete_station,
    get_hospitals, add_hospital, delete_hospital,
    import_stations_from_geojson, import_hospitals_from_geojson,
)
from app.modules.auth import authenticate_user
from app.modules.geo import validate_coordinates
from app.modules.routing import get_route, get_osrm_route_cached
from app.modules.alerts import get_alert_color, get_alert_label, format_time_ago
from streamlit_folium import st_folium

init_db()

st.markdown("""
<style>
    @keyframes blink-border{0%,100%{border-color:rgba(255,0,0,.3)}50%{border-color:rgba(255,0,0,.9)}}
    .cc-header{background:linear-gradient(90deg,#0a0a1a,#1a1a3a 50%,#0a0a1a);border-bottom:2px solid #1a1a4a;padding:.8rem 1.2rem;margin:-1rem -1rem 1rem -1rem;display:flex;justify-content:space-between;align-items:center}
    .cc-title{font-size:1.3rem;font-weight:900;color:#4B8BFF;letter-spacing:3px;text-transform:uppercase;margin:0}
    .cc-clock{color:#0f8;font-family:monospace;font-size:1rem;font-weight:bold}
    .cc-badge{background:#f00;color:#fff;padding:2px 8px;border-radius:4px;font-size:.65rem;font-weight:bold;animation:blink-border 1.5s infinite;border:1px solid transparent;margin-left:.5rem}
    .metric-panel{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #1a1a3a;border-radius:8px;padding:.8rem;text-align:center}
    .metric-num{font-size:1.8rem;font-weight:900;line-height:1}
    .metric-red{color:#f00;text-shadow:0 0 15px rgba(255,0,0,.4)}
    .metric-amber{color:#f80}
    .metric-green{color:#0f8;text-shadow:0 0 10px rgba(0,255,136,.3)}
    .metric-label{font-size:.7rem;color:#666;text-transform:uppercase;letter-spacing:1px;margin-top:.3rem}
    .alert-tile{background:linear-gradient(145deg,#111122,#0a0a1a);border-left:3px solid #f00;border-radius:6px;padding:.8rem;margin-bottom:.5rem;transition:all .2s}
    .alert-tile:hover{background:#1a1a2e;transform:translateX(3px)}
    .alert-tile-resolved{border-left-color:#0f8}
    .alert-tile-progress{border-left-color:#f80}
    .tile-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem}
    .tile-type{font-size:.75rem;font-weight:bold;text-transform:uppercase}
    .tile-time{font-size:.7rem;color:#555;font-family:monospace}
    .tile-coords{font-size:.75rem;color:#777;font-family:monospace}
    .tile-desc{font-size:.8rem;color:#999;margin-top:.3rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .login-box{max-width:420px;margin:3rem auto;background:linear-gradient(145deg,#0a0a1a,#111122);border:1px solid #1a1a3a;border-radius:12px;padding:2rem;box-shadow:0 20px 60px rgba(0,0,0,.5)}
    .login-title{text-align:center;color:#4B8BFF;font-size:1.3rem;font-weight:900;letter-spacing:2px;margin-bottom:1.5rem}
    .footer-co{text-align:center;color:#444;font-size:.75rem;margin-top:2rem;padding:1rem 0;border-top:1px solid #1a1a1a}
    .footer-co a{color:#4B8BFF;text-decoration:none}
    .station-card{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #1a1a3a;border-radius:8px;padding:.8rem;margin-bottom:.5rem;font-size:.8rem}
    .station-active{border-color:#0f8}
    .hospital-card{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #2a2a1a;border-radius:8px;padding:.8rem;margin-bottom:.5rem;font-size:.8rem}
    .hospital-emergency{border-color:#f80}
    .upload-box{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #333;border-radius:8px;padding:1rem;margin-bottom:1rem}
    .select-station{background:linear-gradient(145deg,#1a1a2e,#0d0d1a);border:1px solid #4B8BFF;border-radius:8px;padding:1rem;margin:1rem 0}
    .route-info{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #FF8800;border-radius:8px;padding:.8rem;margin:.5rem 0;font-size:.85rem;color:#ccc}
    .agent-bar{background:linear-gradient(145deg,#0d0d1a,#141428);border:1px solid #1a1a3a;border-radius:8px;padding:.6rem 1rem;margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;font-size:.8rem}
    .agent-name{color:#fff;font-weight:bold}
    .agent-role{color:#888;text-transform:uppercase;font-size:.7rem}
</style>
""", unsafe_allow_html=True)

if "police_user" not in st.session_state:
    st.session_state.police_user = None
if "selected_station_id" not in st.session_state:
    st.session_state.selected_station_id = None
if "zoom_to" not in st.session_state:
    st.session_state.zoom_to = None

# ===== LOGIN =====
if st.session_state.police_user is None:
    st.markdown('<div class="login-box"><div class="login-title">🔐 CENTRE DE COMMANDEMENT</div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        username = st.text_input("IDENTIFIANT", value="officer1")
        password = st.text_input("MOT DE PASSE", type="password", value="Officer2026!")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("CONNEXION", type="primary", use_container_width=True):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.police_user = user
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        with c2:
            if st.button("MODE DEMO", use_container_width=True):
                user = authenticate_user("officer1", "Officer2026!")
                if user:
                    st.session_state.police_user = user
                    st.rerun()
    if st.button("← RETOUR ACCUEIL"):
        st.switch_page("streamlit_app.py")
    st.stop()

user = st.session_state.police_user

# ===== HEADER =====
st.markdown(f"""
<div class="cc-header">
    <div><span class="cc-title">MUTU ALERT - COMMANDEMENT</span><span class="cc-badge">LIVE</span></div>
    <div class="cc-clock">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
</div>""", unsafe_allow_html=True)

# ===== AGENT BAR =====
st.markdown(f"""
<div class="agent-bar">
    <div><span class="agent-name">👮 {user['full_name']}</span> <span class="agent-role">| {user['role'].upper()}</span></div>
    <div><form></form></div>
</div>
""", unsafe_allow_html=True)

# Filter control
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
with col_f1:
    show_status = st.segmented_control(
        "Filtrer",
        ["all", "active", "in_progress", "resolved"],
        format_func=lambda x: {
            "all": "TOUS",
            "active": "ACTIFS",
            "in_progress": "EN COURS",
            "resolved": "RESOLUS",
        }.get(x, x),
        default="all",
        label_visibility="collapsed",
    )
with col_f3:
    if st.button("🚪 DECONNEXION", use_container_width=True):
        st.session_state.police_user = None
        st.rerun()

# ===== DATA =====
stations = get_police_stations()
hospitals = get_hospitals()
default_station = get_default_station()
df_alerts = get_all_alerts(200)
if show_status != "all":
    df_alerts = df_alerts[df_alerts["status"] == show_status]

# ===== STATION SELECTION =====
st.markdown("<div class='select-station'>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#4B8BFF;margin:0 0 .5rem 0'>🏢 Station de Police Active</h4>", unsafe_allow_html=True)

station_options = {
    row["id"]: f"#{row['id']} {row['name']} ({row['latitude']:.4f}, {row['longitude']:.4f})"
    for _, row in stations.iterrows()
}
if default_station is not None and st.session_state.selected_station_id is None:
    st.session_state.selected_station_id = int(default_station["id"])

if station_options:
    selected_id = st.selectbox(
        "Choisir le poste pour les interventions",
        options=list(station_options.keys()),
        format_func=lambda x: station_options.get(x, "?"),
        index=list(station_options.keys()).index(st.session_state.selected_station_id)
        if st.session_state.selected_station_id in station_options
        else 0,
    )
    st.session_state.selected_station_id = selected_id
else:
    st.warning("Aucune station configuree. Ajoutez-en dans l'onglet Postes.")
    selected_id = None

st.markdown("</div>", unsafe_allow_html=True)

# Get active station coords
active_station = get_station_by_id(st.session_state.selected_station_id) if selected_id else None
if active_station is not None:
    police_lat = float(active_station["latitude"])
    police_lon = float(active_station["longitude"])
    police_name = active_station["name"]
else:
    police_lat, police_lon = -4.3250, 15.3222
    police_name = "Police"

# ===== METRICS =====
m1, m2, m3, m4 = st.columns(4)
ac = len(df_alerts[df_alerts["status"] == "active"])
ip = len(df_alerts[df_alerts["status"] == "in_progress"])
rc = len(df_alerts[df_alerts["status"] == "resolved"])
tc = len(df_alerts)
with m1:
    st.markdown(f'<div class="metric-panel"><div class="metric-num metric-red">{ac}</div><div class="metric-label">Actives</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-panel"><div class="metric-num metric-amber">{ip}</div><div class="metric-label">En Cours</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-panel"><div class="metric-num metric-green">{rc}</div><div class="metric-label">Resolues</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-panel"><div class="metric-num" style="color:#4B8BFF">{tc}</div><div class="metric-label">Total</div></div>', unsafe_allow_html=True)

st.divider()

# ===== TABS =====
tab_map, tab_stations, tab_hospitals = st.tabs(["🗺 Carte & Alertes", "🏢 Postes de Police", "🏥 Hopitaux"])

with tab_stations:
    st.subheader("Gestion des Postes de Police")
    active_info = f"**#{active_station['id']} {police_name}** ({police_lat:.5f}, {police_lon:.5f})" if active_station is not None else "Non defini"
    st.info("Poste actif pour les trajets : " + active_info)

    col_up, col_list = st.columns([1, 2])
    with col_up:
        st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
        st.markdown("<b>📁 Importer GeoJSON</b>", unsafe_allow_html=True)
        geo_file = st.file_uploader("Fichier .geojson ou .json", type=["geojson", "json"], key="up_station")
        if geo_file:
            try:
                gdata = json.load(geo_file)
                n = import_stations_from_geojson(gdata)
                st.success(f"✅ {n} postes importes")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
        st.markdown("<b>➕ Ajouter manuellement</b>", unsafe_allow_html=True)
        s_name = st.text_input("Nom", key="s_name", placeholder="Commissariat...")
        s_lat = st.number_input("Latitude", value=-4.3250, format="%.6f", key="s_lat")
        s_lon = st.number_input("Longitude", value=15.3222, format="%.6f", key="s_lon")
        s_addr = st.text_input("Adresse", key="s_addr")
        s_phone = st.text_input("Telephone", key="s_phone")
        s_default = st.checkbox("Definir comme actif", value=False, key="s_default")
        if st.button("Ajouter", type="primary", key="add_s_btn"):
            add_police_station(s_name, s_lat, s_lon, s_addr, s_phone, s_default)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_list:
        st.markdown("<b>📋 Liste des postes</b>", unsafe_allow_html=True)
        for idx, stn in stations.iterrows():
            active_badge = " 🟢 ACTIF" if stn["id"] == st.session_state.selected_station_id else (" 🟢 DEFAUT" if stn["is_default"] else "")
            st.markdown(f"""
            <div class="station-card{' station-active' if stn['id']==st.session_state.selected_station_id else ''}">
                <b>#{stn['id']} {stn['name']}{active_badge}</b><br>
                📍 {stn['latitude']:.5f}, {stn['longitude']:.5f}<br>
                {stn['address'] or 'N/A'} | 📞 {stn['phone'] or 'N/A'}
            </div>""", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"Definir actif", key=f"setact_{stn['id']}", use_container_width=True):
                    st.session_state.selected_station_id = int(stn["id"])
                    st.rerun()
            with c2:
                if not stn["is_default"] and st.button(f"Defaut", key=f"setdef_{stn['id']}", use_container_width=True):
                    update_station_default(stn["id"])
                    st.rerun()
            with c3:
                if st.button(f"Suppr", key=f"dels_{stn['id']}", use_container_width=True):
                    delete_station(stn["id"])
                    st.rerun()

with tab_hospitals:
    st.subheader("Gestion des Hopitaux")
    col_uph, col_listh = st.columns([1, 2])
    with col_uph:
        st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
        st.markdown("<b>📁 Importer Hopitaux GeoJSON</b>", unsafe_allow_html=True)
        hgeo_file = st.file_uploader("Fichier .geojson ou .json", type=["geojson", "json"], key="up_hosp")
        if hgeo_file:
            try:
                hdata = json.load(hgeo_file)
                n = import_hospitals_from_geojson(hdata)
                st.success(f"✅ {n} hopitaux importes")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
        st.markdown("<b>➕ Ajouter manuellement</b>", unsafe_allow_html=True)
        h_name = st.text_input("Nom", key="h_name", placeholder="Hopital...")
        h_lat = st.number_input("Latitude", value=-4.3250, format="%.6f", key="h_lat")
        h_lon = st.number_input("Longitude", value=15.3120, format="%.6f", key="h_lon")
        h_addr = st.text_input("Adresse", key="h_addr")
        h_phone = st.text_input("Telephone", key="h_phone")
        h_emer = st.checkbox("Urgences 24/7", value=True, key="h_emer")
        if st.button("Ajouter hopital", type="primary", key="add_h_btn"):
            add_hospital(h_name, h_lat, h_lon, h_addr, h_phone, h_emer)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_listh:
        st.markdown("<b>📋 Liste des hopitaux</b>", unsafe_allow_html=True)
        for idx, hos in hospitals.iterrows():
            emer_badge = " 🚨 URGENCES" if hos["emergency"] else ""
            st.markdown(f"""
            <div class="hospital-card{' hospital-emergency' if hos['emergency'] else ''}">
                <b>#{hos['id']} {hos['name']}{emer_badge}</b><br>
                📍 {hos['latitude']:.5f}, {hos['longitude']:.5f}<br>
                {hos['address'] or 'N/A'} | 📞 {hos['phone'] or 'N/A'}
            </div>""", unsafe_allow_html=True)
            if st.button(f"Suppr #{hos['id']}", key=f"delh_{hos['id']}", use_container_width=True):
                delete_hospital(hos["id"])
                st.rerun()

with tab_map:
    left, right = st.columns([3, 2])

    with left:
        st.markdown(f"<div style='color:#888;font-size:.75rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:.5rem'>🗺 Carte - Depuis : {police_name}</div>", unsafe_allow_html=True)

        if st.session_state.zoom_to and len(df_alerts) > 0:
            za = df_alerts[df_alerts["id"] == st.session_state.zoom_to]
            if len(za) > 0:
                center_lat, center_lon = za.iloc[0]["latitude"], za.iloc[0]["longitude"]
                zoom_level = 16
            else:
                center_lat, center_lon, zoom_level = police_lat, police_lon, 13
        else:
            center_lat, center_lon, zoom_level = police_lat, police_lon, 13

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles="CartoDB dark_matter",
        )

        # Active station
        folium.Marker(
            [police_lat, police_lon],
            icon=folium.Icon(color="darkblue", icon="shield", prefix="fa"),
            popup=f"<b>Poste actif: {police_name}</b>",
            tooltip=f"🚔 {police_name}",
        ).add_to(m)
        folium.Circle(
            [police_lat, police_lon],
            radius=400,
            fill=True,
            color="#4B8BFF",
            fill_color="#4B8BFF",
            fill_opacity=0.1,
        ).add_to(m)

        # Hospitals
        for _, hos in hospitals.iterrows():
            folium.Marker(
                [hos["latitude"], hos["longitude"]],
                icon=folium.Icon(color="pink", icon="plus", prefix="fa"),
                popup=f"Hopital: {hos['name']}",
                tooltip=f"🏥 {hos['name']}",
            ).add_to(m)

        # Alert markers
        for idx, alert in df_alerts.iterrows():
            color = get_alert_color(alert["alert_type"])
            label = get_alert_label(alert["alert_type"])
            status = alert["status"]
            lat, lon = alert["latitude"], alert["longitude"]
            is_zoomed = st.session_state.zoom_to == alert["id"]

            if status == "active":
                folium.CircleMarker(
                    [lat, lon],
                    radius=10,
                    fill=True,
                    color="#FF0000",
                    fill_color="#FF0000",
                    fill_opacity=0.6,
                ).add_to(m)
                folium.Circle(
                    [lat, lon],
                    radius=80,
                    fill=True,
                    color="#FF0000",
                    fill_color="#FF0000",
                    fill_opacity=0.3 if is_zoomed else 0.15,
                ).add_to(m)
                if is_zoomed:
                    folium.Circle(
                        [lat, lon],
                        radius=150,
                        fill=True,
                        color="#FF0000",
                        fill_color="#FF0000",
                        fill_opacity=0.15,
                    ).add_to(m)
                folium.Marker(
                    [lat, lon],
                    icon=folium.Icon(color="red", icon="exclamation", prefix="fa"),
                    popup=folium.Popup(
                        f"""<div style="font-family:sans-serif;min-width:200px;color:#fff;background:#111;padding:10px;border-radius:6px;border-left:3px solid {color}">
                        <h4 style="color:{color};margin:0;font-size:1rem">🚨 {label} #{alert['id']}</h4>
                        <hr style="border-color:#333;margin:6px 0">
                        <p style="margin:4px 0;font-size:.8rem;color:#ccc"><b style="color:#fff">Status:</b> <span style="color:#f00;font-weight:bold">ACTIVE</span></p>
                        <p style="margin:4px 0;font-size:.8rem;color:#ccc"><b style="color:#fff">Heure:</b> {alert['created_at']}</p>
                        <p style="margin:4px 0;font-size:.8rem;color:#ccc"><b style="color:#fff">Desc:</b> {str(alert['description']) if alert['description'] else 'N/A'}</p>
                        <p style="margin:4px 0;font-size:.8rem;color:#ccc"><b style="color:#fff">Tel:</b> {alert['phone'] or 'Anonyme'}</p></div>""",
                        max_width=320,
                    ),
                    tooltip=f"🔴 #{alert['id']} {label}",
                ).add_to(m)
            elif status == "in_progress":
                folium.Marker(
                    [lat, lon],
                    icon=folium.Icon(color="orange", icon="car", prefix="fa"),
                    tooltip=f"🟡 #{alert['id']} En cours",
                ).add_to(m)
                if alert["route_data"]:
                    try:
                        route = json.loads(alert["route_data"])
                        if isinstance(route, list) and len(route) > 1:
                            folium.PolyLine(route, color="#FF8800", weight=5, opacity=0.9).add_to(m)
                    except Exception:
                        pass
            else:
                folium.Marker(
                    [lat, lon],
                    icon=folium.Icon(color="green", icon="check", prefix="fa"),
                    tooltip=f"🟢 #{alert['id']} Resolu",
                ).add_to(m)

        # OSRM routes from selected station to active alerts (cached)
        active_alerts = df_alerts[df_alerts["status"] == "active"]
        for idx, alert in active_alerts.iterrows():
            route_pts, dist_km, dur_min = get_route(police_lat, police_lon, alert["latitude"], alert["longitude"], use_cache=True)
            if route_pts:
                folium.PolyLine(route_pts, color="#FF0000", weight=3, opacity=0.5, dash_array="5,10").add_to(m)

        st_folium(m, width=700, height=550, returned_objects=[])

    with right:
        st.markdown("<div style='color:#888;font-size:.75rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:.5rem'>📋 Alertes</div>", unsafe_allow_html=True)
        if len(df_alerts) == 0:
            st.info("Aucune alerte.")
        else:
            for idx, alert in df_alerts.head(15).iterrows():
                color = get_alert_color(alert["alert_type"])
                label = get_alert_label(alert["alert_type"])
                tile_class = "alert-tile"
                if alert["status"] == "resolved":
                    tile_class += " alert-tile-resolved"
                elif alert["status"] == "in_progress":
                    tile_class += " alert-tile-progress"

                time_ago = format_time_ago(alert["created_at"]) if isinstance(alert["created_at"], str) else "now"
                desc = str(alert["description"])
                if desc in ("None", ""):
                    desc = "Pas de description"
                elif len(desc) > 50:
                    desc = desc[:50] + "..."

                st.markdown(
                    f"""<div class="{tile_class}"><div class="tile-header">
                    <span class="tile-type" style="color:{color}">#{alert['id']} {label}</span>
                    <span class="tile-time">{time_ago}</span></div>
                    <div class="tile-coords">📍 {alert['latitude']:.5f}, {alert['longitude']:.5f}</div>
                    <div class="tile-desc">{desc}</div></div>""",
                    unsafe_allow_html=True,
                )

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button("🔍 ZOOM", key=f"zoom_{alert['id']}", use_container_width=True):
                        st.session_state.zoom_to = alert["id"]
                        st.rerun()
                with c2:
                    if alert["status"] == "active" and st.button("🚀 PRENDRE", key=f"take_{alert['id']}", use_container_width=True):
                        route_pts, dist_km, dur_min = get_route(police_lat, police_lon, alert["latitude"], alert["longitude"])
                        if route_pts:
                            add_route_data(alert["id"], json.dumps(route_pts), user["username"])
                        update_alert_status(alert["id"], "in_progress", user["username"])
                        msg = f"Intervention lancee! {dist_km:.1f}km / {dur_min:.0f}min" if dist_km else "Intervention lancee!"
                        st.toast(msg)
                        time.sleep(0.3)
                        st.rerun()
                with c3:
                    if alert["status"] == "in_progress" and st.button("✅ RESOUDRE", key=f"resolve_{alert['id']}", use_container_width=True):
                        update_alert_status(alert["id"], "resolved", user["username"])
                        st.toast("Resolu!")
                        time.sleep(0.3)
                        st.rerun()
                with c4:
                    if st.button("🗺 ROUTE", key=f"route_{alert['id']}", use_container_width=True):
                        route_pts, dist_km, dur_min = get_route(police_lat, police_lon, alert["latitude"], alert["longitude"])
                        if route_pts:
                            add_route_data(alert["id"], json.dumps(route_pts), user["username"])
                            st.toast(f"Route: {dist_km:.1f}km, {dur_min:.0f}min")
                        else:
                            st.toast("Route calculee (fallback)")
                        st.rerun()

st.divider()
with st.expander("📜 JOURNAL D'ACTIVITE (AUDIT)"):
    from app.modules.database import get_db
    with get_db() as conn:
        logs = pd.read_sql_query(
            """SELECT al.*, a.latitude, a.longitude
            FROM alert_logs al JOIN alerts a ON al.alert_id=a.id
            ORDER BY al.timestamp DESC LIMIT 50""",
            conn,
        )
    if len(logs) > 0:
        st.dataframe(logs[["timestamp", "alert_id", "action", "performed_by"]], use_container_width=True, hide_index=True)
    else:
        st.info("Aucune activite")

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
if st.button("← RETOUR ACCUEIL"):
    st.switch_page("streamlit_app.py")

st.markdown(
    """<div class="footer-co"><b>MutuAlert</b> &copy; 2026 | Powered by
    <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves</div>""",
    unsafe_allow_html=True,
)
