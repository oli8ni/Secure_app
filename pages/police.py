import streamlit as st
import folium
import json
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="MutuAlert - Centre de Commandement", page_icon="👮", layout="wide")

# === HIDE SIDEBAR COMPLETELY ===
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

from app.modules.database import init_db, get_active_alerts, get_all_alerts, update_alert_status, add_route_data
from app.modules.auth import authenticate_user, logout
from app.modules.geo import validate_coordinates, generate_route_points
from app.modules.alerts import get_alert_color, get_alert_label, create_blinking_marker_js, format_time_ago
from streamlit_folium import st_folium

init_db()

st.markdown("""
<style>
    @keyframes blink-border {
        0%, 100% { border-color: rgba(255,0,0,0.3); }
        50% { border-color: rgba(255,0,0,0.9); }
    }
    .cc-header {
        background: linear-gradient(90deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a1a 100%);
        border-bottom: 2px solid #1a1a4a;
        padding: 0.8rem 1.2rem;
        margin: -1rem -1rem 1rem -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .cc-title {
        font-size: 1.3rem;
        font-weight: 900;
        color: #4B8BFF;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0;
    }
    .cc-clock {
        color: #00ff88;
        font-family: monospace;
        font-size: 1rem;
        font-weight: bold;
    }
    .cc-badge {
        background: #FF0000;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: bold;
        animation: blink-border 1.5s infinite;
        border: 1px solid transparent;
        margin-left: 0.5rem;
    }
    .metric-panel {
        background: linear-gradient(145deg, #0d0d1a, #141428);
        border: 1px solid #1a1a3a;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
    .metric-num {
        font-size: 1.8rem;
        font-weight: 900;
        line-height: 1;
    }
    .metric-red { color: #FF0000; text-shadow: 0 0 15px rgba(255,0,0,0.4); }
    .metric-amber { color: #FF8800; }
    .metric-green { color: #00ff88; text-shadow: 0 0 10px rgba(0,255,136,0.3); }
    .metric-label {
        font-size: 0.7rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
    .alert-tile {
        background: linear-gradient(145deg, #111122, #0a0a1a);
        border-left: 3px solid #FF0000;
        border-radius: 6px;
        padding: 0.8rem;
        margin-bottom: 0.5rem;
        transition: all 0.2s;
    }
    .alert-tile:hover {
        background: #1a1a2e;
        transform: translateX(3px);
    }
    .alert-tile-resolved { border-left-color: #00ff88; }
    .alert-tile-progress { border-left-color: #FF8800; }
    .tile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.3rem;
    }
    .tile-type {
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .tile-time {
        font-size: 0.7rem;
        color: #555;
        font-family: monospace;
    }
    .tile-coords {
        font-size: 0.75rem;
        color: #777;
        font-family: monospace;
    }
    .tile-desc {
        font-size: 0.8rem;
        color: #999;
        margin-top: 0.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .login-box {
        max-width: 420px;
        margin: 3rem auto;
        background: linear-gradient(145deg, #0a0a1a, #111122);
        border: 1px solid #1a1a3a;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .login-title {
        text-align: center;
        color: #4B8BFF;
        font-size: 1.3rem;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 1.5rem;
    }
    .footer-co {
        text-align: center;
        color: #444;
        font-size: 0.75rem;
        margin-top: 2rem;
        padding: 1rem 0;
        border-top: 1px solid #1a1a1a;
    }
    .footer-co a {
        color: #4B8BFF;
        text-decoration: none;
    }
    .upload-box {
        background: linear-gradient(145deg, #0d0d1a, #141428);
        border: 1px solid #1a1a3a;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

if 'police_user' not in st.session_state:
    st.session_state.police_user = None

if st.session_state.police_user is None:
    st.markdown("""
    <div class="login-box">
        <div class="login-title">🔐 CENTRE DE COMMANDEMENT</div>
        <p style="text-align:center; color:#666; font-size:0.85rem; margin-top:-1rem; margin-bottom:1.5rem;">
            Acces securise - Forces de l'Ordre
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
        [data-testid="stTextInput"] label { color: #4B8BFF !important; font-size: 0.75rem !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
        [data-testid="stTextInput"] input { background: #0d0d1a !important; border: 1px solid #1a1a3a !important; color: #fff !important; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("IDENTIFIANT", value="officer1")
        password = st.text_input("MOT DE PASSE", type="password", value="Officer2026!")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("CONNEXION", type="primary", use_container_width=True):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.police_user = user
                    st.success(f"Bienvenue {user['full_name']}")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        with c2:
            if st.button("MODE DEMO", use_container_width=True):
                user = authenticate_user("officer1", "Officer2026!")
                if user:
                    st.session_state.police_user = user
                    st.rerun()
    
    st.markdown("""
    <div style="text-align:center; margin-top:1rem; color:#444; font-size:0.75rem;">
        Comptes demo: officer1 / Officer2026! | admin / Police2026!
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← RETOUR ACCUEIL"):
        st.switch_page("streamlit_app.py")
    st.stop()

user = st.session_state.police_user

st.markdown(f"""
<div class="cc-header">
    <div>
        <span class="cc-title">MUTU ALERT - COMMANDEMENT</span>
        <span class="cc-badge">LIVE</span>
    </div>
    <div class="cc-clock">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, #0d0d1a, #141428); border-radius:8px; padding:1rem; margin-bottom:1rem; border:1px solid #1a1a3a;">
        <div style="color:#4B8BFF; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px;">Agent Connecte</div>
        <div style="color:#fff; font-weight:bold; font-size:1rem;">{user['full_name']}</div>
        <div style="color:#888; font-size:0.75rem;">{user['role'].upper()} | {user['station'] or 'CENTRAL'}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 DECONNEXION", use_container_width=True):
        st.session_state.police_user = None
        st.rerun()
    
    st.divider()
    st.markdown("<div style='color:#4B8BFF; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;'>Filtres</div>", unsafe_allow_html=True)
    show_status = st.segmented_control("", 
        ["all", "active", "in_progress", "resolved"],
        format_func=lambda x: {"all": "TOUS", "active": "ACTIFS", "in_progress": "EN COURS", "resolved": "RESOLUS"}.get(x, x),
        default="all"
    )

df_alerts = get_all_alerts(200)
if show_status != "all":
    df_alerts = df_alerts[df_alerts['status'] == show_status]

# Zoom state
if 'zoom_to' not in st.session_state:
    st.session_state.zoom_to = None

# Metrics
m1, m2, m3, m4 = st.columns(4)
active_count = len(df_alerts[df_alerts['status'] == 'active'])
in_progress_count = len(df_alerts[df_alerts['status'] == 'in_progress'])
resolved_count = len(df_alerts[df_alerts['status'] == 'resolved'])
total_count = len(df_alerts)

with m1:
    st.markdown(f'<div class="metric-panel"><div class="metric-num metric-red">{active_count}</div><div class="metric-label">Alertes Actives</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-panel"><div class="metric-num metric-amber">{in_progress_count}</div><div class="metric-label">En Cours</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-panel"><div class="metric-num metric-green">{resolved_count}</div><div class="metric-label">Resolues 24h</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-panel"><div class="metric-num" style="color:#4B8BFF;">{total_count}</div><div class="metric-label">Total</div></div>', unsafe_allow_html=True)

st.divider()

left, right = st.columns([3, 2])

# === MAP ===
with left:
    st.markdown("<div style='color:#888; font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:0.5rem;'>🗺 Carte Temps Reel</div>", unsafe_allow_html=True)
    
    # Upload GeoJSON
    with st.expander("📁 Charger centres de police (GeoJSON)"):
        geojson_file = st.file_uploader("Fichier .geojson", type=['geojson', 'json'])
        police_stations = []
        if geojson_file:
            try:
                geojson_data = json.load(geojson_file)
                if 'features' in geojson_data:
                    for feat in geojson_data['features']:
                        if feat.get('geometry', {}).get('type') == 'Point':
                            coords = feat['geometry']['coordinates']
                            name = feat.get('properties', {}).get('name', f"Poste {len(police_stations)+1}")
                            police_stations.append({'name': name, 'lon': coords[0], 'lat': coords[1]})
                st.success(f"{len(police_stations)} centres de police charges")
            except Exception as e:
                st.error(f"Erreur lecture GeoJSON: {e}")
    
    # Determine center
    if st.session_state.zoom_to and len(df_alerts) > 0:
        z_alert = df_alerts[df_alerts['id'] == st.session_state.zoom_to]
        if len(z_alert) > 0:
            center_lat = z_alert.iloc[0]['latitude']
            center_lon = z_alert.iloc[0]['longitude']
            zoom_level = 16
        else:
            center_lat = df_alerts['latitude'].mean() if len(df_alerts) > 0 else 5.3600
            center_lon = df_alerts['longitude'].mean() if len(df_alerts) > 0 else -4.0083
            zoom_level = 13
    elif len(df_alerts) > 0:
        center_lat = df_alerts['latitude'].mean()
        center_lon = df_alerts['longitude'].mean()
        zoom_level = 13
    else:
        center_lat, center_lon = 5.3600, -4.0083
        zoom_level = 13
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, tiles="CartoDB dark_matter")
    
    # Pulsing CSS
    pulse_css = """
    <style>
    @keyframes map-pulse {
        0% { r: 12; stroke-opacity: 0.8; fill-opacity: 0.4; }
        50% { r: 35; stroke-opacity: 0.2; fill-opacity: 0.1; }
        100% { r: 12; stroke-opacity: 0.8; fill-opacity: 0.4; }
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(pulse_css))
    
    # HQ marker
    folium.Marker([center_lat, center_lon], icon=folium.Icon(color='darkblue', icon='building', prefix='fa'), tooltip="POSTE DE COMMANDEMENT").add_to(m)
    
    # Police stations from GeoJSON
    for station in police_stations:
        folium.Marker([station['lat'], station['lon']], 
            icon=folium.Icon(color='blue', icon='shield', prefix='fa'),
            popup=f"Police: {station['name']}",
            tooltip=f"🚔 {station['name']}"
        ).add_to(m)
    
    for idx, alert in df_alerts.iterrows():
        color = get_alert_color(alert['alert_type'])
        label = get_alert_label(alert['alert_type'])
        status = alert['status']
        lat, lon = alert['latitude'], alert['longitude']
        is_zoomed = st.session_state.zoom_to == alert['id']
        
        if status == 'active':
            # Pulsing circles for active alerts
            folium.CircleMarker([lat, lon], radius=12, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.4).add_to(m)
            folium.CircleMarker([lat, lon], radius=35, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.08).add_to(m)
            if is_zoomed:
                folium.Circle([lat, lon], radius=100, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.15).add_to(m)
            folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='exclamation', prefix='fa'),
                popup=folium.Popup(f"""<div style="font-family:sans-serif;min-width:200px;color:#fff;background:#111;padding:10px;border-radius:6px;border-left:3px solid {color};"><h4 style="color:{color};margin:0;font-size:1rem;">🚨 {label} #{alert['id']}</h4><hr style="border-color:#333;margin:6px 0;"><p style="margin:4px 0;font-size:0.8rem;color:#ccc;"><b style="color:#fff;">Status:</b> <span style="color:#ff0000;font-weight:bold;">ACTIVE</span></p><p style="margin:4px 0;font-size:0.8rem;color:#ccc;"><b style="color:#fff;">Heure:</b> {alert['created_at']}</p><p style="margin:4px 0;font-size:0.8rem;color:#ccc;"><b style="color:#fff;">Desc:</b> {str(alert['description']) if alert['description'] else 'Non specifie'}</p><p style="margin:4px 0;font-size:0.8rem;color:#ccc;"><b style="color:#fff;">Tel:</b> {alert['phone'] or 'Anonyme'}</p></div>""", max_width=320),
                tooltip=f"🔴 #{alert['id']} {label}"
            ).add_to(m)
        elif status == 'in_progress':
            folium.Marker([lat, lon], icon=folium.Icon(color='orange', icon='car', prefix='fa'), popup=f"Intervention #{alert['id']}", tooltip=f"🟡 #{alert['id']} En cours").add_to(m)
            if alert['route_data']:
                try:
                    route = json.loads(alert['route_data'])
                    if isinstance(route, list) and len(route) > 1:
                        folium.PolyLine(route, color='#FF8800', weight=5, opacity=0.9, popup=f"Route #{alert['id']}").add_to(m)
                except:
                    pass
        else:
            folium.Marker([lat, lon], icon=folium.Icon(color='green', icon='check', prefix='fa'), popup=f"Resolu #{alert['id']}", tooltip=f"🟢 #{alert['id']} Resolu").add_to(m)
    
    # Routes from HQ to active alerts
    for idx, alert in df_alerts[df_alerts['status'] == 'active'].iterrows():
        route_pts = generate_route_points(center_lat, center_lon, alert['latitude'], alert['longitude'], num_points=15)
        folium.PolyLine(route_pts, color='#FF0000', weight=2, opacity=0.3, dash_array='5, 10').add_to(m)
    
    st_folium(m, width=700, height=550, returned_objects=[])

# === ALERT LIST ===
with right:
    st.markdown("<div style='color:#888; font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:0.5rem;'>📋 Liste des Alertes</div>", unsafe_allow_html=True)
    
    if len(df_alerts) == 0:
        st.info("Aucune alerte.")
    else:
        for idx, alert in df_alerts.head(15).iterrows():
            color = get_alert_color(alert['alert_type'])
            label = get_alert_label(alert['alert_type'])
            tile_class = "alert-tile"
            if alert['status'] == 'resolved':
                tile_class += " alert-tile-resolved"
            elif alert['status'] == 'in_progress':
                tile_class += " alert-tile-progress"
            time_ago = format_time_ago(alert['created_at']) if isinstance(alert['created_at'], str) else "now"
            
            desc_display = str(alert['description'])
            if len(desc_display) > 50:
                desc_display = desc_display[:50] + '...'
            elif not desc_display or desc_display == 'None':
                desc_display = 'Pas de description'
            
            st.markdown(f"""
            <div class="{tile_class}">
                <div class="tile-header">
                    <span class="tile-type" style="color:{color};">#{alert['id']} {label}</span>
                    <span class="tile-time">{time_ago}</span>
                </div>
                <div class="tile-coords">📍 {alert['latitude']:.5f}, {alert['longitude']:.5f}</div>
                <div class="tile-desc">{desc_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # BOUTON ZOOMER + actions
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("🔍 ZOOMER", key=f"zoom_{alert['id']}", use_container_width=True):
                    st.session_state.zoom_to = alert['id']
                    st.rerun()
            with c2:
                if alert['status'] == 'active' and st.button("🚀 PRENDRE", key=f"take_{alert['id']}", use_container_width=True):
                    update_alert_status(alert['id'], 'in_progress', user['username'])
                    route = generate_route_points(center_lat, center_lon, alert['latitude'], alert['longitude'])
                    add_route_data(alert['id'], json.dumps(route), user['username'])
                    st.toast("Intervention lancee!")
                    time.sleep(0.3)
                    st.rerun()
            with c3:
                if alert['status'] == 'in_progress' and st.button("✅ RESOUDRE", key=f"resolve_{alert['id']}", use_container_width=True):
                    update_alert_status(alert['id'], 'resolved', user['username'])
                    st.toast("Alerte resolue!")
                    time.sleep(0.3)
                    st.rerun()
            with c4:
                if st.button("🗺 ROUTE", key=f"route_{alert['id']}", use_container_width=True):
                    route = generate_route_points(center_lat, center_lon, alert['latitude'], alert['longitude'])
                    add_route_data(alert['id'], json.dumps(route), user['username'])
                    st.toast("Itineraire calcule")
                    st.rerun()

st.divider()
with st.expander("📜 JOURNAL D'ACTIVITE (AUDIT)"):
    from app.modules.database import get_db
    with get_db() as conn:
        import pandas as pd
        logs = pd.read_sql_query("""
            SELECT al.*, a.latitude, a.longitude 
            FROM alert_logs al
            JOIN alerts a ON al.alert_id = a.id
            ORDER BY al.timestamp DESC
            LIMIT 50
        """, conn)
    
    if len(logs) > 0:
        st.dataframe(logs[['timestamp', 'alert_id', 'action', 'performed_by', 'latitude', 'longitude']], use_container_width=True, hide_index=True)
    else:
        st.info("Aucune activite enregistree")

st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

if st.button("← RETOUR ACCUEIL"):
    st.switch_page("streamlit_app.py")

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves
</div>
""", unsafe_allow_html=True)
