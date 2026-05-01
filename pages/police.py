import streamlit as st
import folium
from folium.plugins import MarkerCluster
import json
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Portail Police", page_icon="👮", layout="wide")

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
.police-header {
    background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    color: white;
}
.alert-card {
    background: #1C1E26;
    border-left: 4px solid #FF0000;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
}
.alert-card:hover {
    background: #2C2E3A;
    transform: translateX(4px);
}
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
}
.status-active { background: #FF0000; color: white; }
.status-in_progress { background: #FF8800; color: black; }
.status-resolved { background: #00AA00; color: white; }
</style>
""", unsafe_allow_html=True)

if 'police_user' not in st.session_state:
    st.session_state.police_user = None

if st.session_state.police_user is None:
    st.markdown("""
    <div class="police-header">
        <h1 style="margin:0;">👮 Portail Sécurité</h1>
        <p style="margin:0; opacity:0.8;">Accès réservé aux forces de l'ordre</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.subheader("Connexion sécurisée")
        username = st.text_input("Identifiant", value="officer1")
        password = st.text_input("Mot de passe", type="password", value="Officer2026!")
        
        col_login, col_demo = st.columns(2)
        with col_login:
            if st.button("Se connecter", type="primary", use_container_width=True):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.police_user = user
                    st.success(f"Bienvenue, {user['full_name']} !")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        with col_demo:
            if st.button("Mode Démo", use_container_width=True):
                user = authenticate_user("officer1", "Officer2026!")
                if user:
                    st.session_state.police_user = user
                    st.rerun()
    
    st.divider()
    st.info("""
    **Comptes de démonstration:**
    - `admin` / `Police2026!` (Administrateur)
    - `officer1` / `Officer2026!` (Agent)
    """)
    
    if st.button("← Retour à l'accueil", key="back_home_police"):
        st.switch_page("streamlit_app.py")
    st.stop()

user = st.session_state.police_user

st.markdown(f"""
<div class="police-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="margin:0;">👮 Centre de Commandement - {user['station'] or 'Central'}</h2>
            <p style="margin:0; opacity:0.8;">Agent: {user['full_name']} | Rôle: {user['role']}</p>
        </div>
        <div>
            <span style="font-size: 0.9rem; opacity:0.8;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.button("🚪 Déconnexion", on_click=lambda: st.session_state.update({"police_user": None}) or st.rerun())

st.sidebar.divider()
st.sidebar.subheader("Filtres")
show_status = st.sidebar.segmented_control("Statut", 
    ["all", "active", "in_progress", "resolved"],
    format_func=lambda x: {"all": "Tous", "active": "Actifs 🔴", "in_progress": "En cours 🟡", "resolved": "Résolus 🟢"}.get(x, x),
    default="all"
)

df_alerts = get_all_alerts(200)
if show_status != "all":
    df_alerts = df_alerts[df_alerts['status'] == show_status]

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
active_count = len(df_alerts[df_alerts['status'] == 'active'])
in_progress_count = len(df_alerts[df_alerts['status'] == 'in_progress'])
resolved_count = len(df_alerts[df_alerts['status'] == 'resolved'])
total_count = len(df_alerts)

with col_stat1:
    st.metric("🔴 Actives", active_count, delta_color="inverse")
with col_stat2:
    st.metric("🟡 En cours", in_progress_count)
with col_stat3:
    st.metric("🟢 Résolues (24h)", resolved_count)
with col_stat4:
    st.metric("📊 Total", total_count)

st.divider()

col_map, col_alerts = st.columns([3, 2])

with col_map:
    st.subheader("🗺 Carte des Alertes en Temps Réel")
    
    if len(df_alerts) > 0:
        center_lat = df_alerts['latitude'].mean()
        center_lon = df_alerts['longitude'].mean()
    else:
        center_lat, center_lon = 48.8566, 2.3522
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB dark_matter")
    blinking_css = create_blinking_marker_js()
    m.get_root().html.add_child(folium.Element(blinking_css))
    
    folium.Marker([center_lat, center_lon], icon=folium.Icon(color='blue', icon='building', prefix='fa'), popup="Poste de Commandement", tooltip="HQ").add_to(m)
    
    for idx, alert in df_alerts.iterrows():
        color = get_alert_color(alert['alert_type'])
        label = get_alert_label(alert['alert_type'])
        status = alert['status']
        
        if status == 'active':
            folium.CircleMarker(location=[alert['latitude'], alert['longitude']], radius=25, fill=True, color=color, fill_color=color, fill_opacity=0.3, popup=f"Zone d'alerte #{alert['id']}").add_to(m)
            folium.Marker(location=[alert['latitude'], alert['longitude']], icon=folium.Icon(color='red', icon='exclamation', prefix='fa'), popup=folium.Popup(f"""<div style="font-family:sans-serif; min-width:200px;"><h4 style="color:{color}; margin:0;">🚨 {label} #{alert['id']}</h4><p><b>Status:</b> <span style="color:{color};">{status.upper()}</span></p><p><b>Heure:</b> {alert['created_at']}</p><p><b>Description:</b> {alert['description'] or 'Non spécifié'}</p><p><b>Tél:</b> {alert['phone'] or 'Anonyme'}</p></div>""", max_width=300), tooltip=f"#{alert['id']} - {label}").add_to(m)
        elif status == 'in_progress':
            folium.Marker(location=[alert['latitude'], alert['longitude']], icon=folium.Icon(color='orange', icon='car', prefix='fa'), popup=f"Intervention en cours #{alert['id']}").add_to(m)
            if alert['route_data']:
                try:
                    route = json.loads(alert['route_data'])
                    if isinstance(route, list) and len(route) > 1:
                        folium.PolyLine(route, color='#FF8800', weight=4, opacity=0.8, popup=f"Itinéraire #{alert['id']}").add_to(m)
                except:
                    pass
        else:
            folium.Marker(location=[alert['latitude'], alert['longitude']], icon=folium.Icon(color='green', icon='check', prefix='fa'), popup=f"Résolu #{alert['id']}").add_to(m)
    
    for idx, alert in df_alerts[df_alerts['status'] == 'active'].iterrows():
        route_pts = generate_route_points(center_lat, center_lon, alert['latitude'], alert['longitude'], num_points=15)
        folium.PolyLine(route_pts, color='#FF0000', weight=2, opacity=0.4, dash_array='5, 10').add_to(m)
    
    st_folium(m, width=700, height=500, returned_objects=[])

with col_alerts:
    st.subheader("📋 Liste des Alertes")
    
    if len(df_alerts) == 0:
        st.info("Aucune alerte pour les critères sélectionnés.")
    else:
        for idx, alert in df_alerts.head(20).iterrows():
            color = get_alert_color(alert['alert_type'])
            label = get_alert_label(alert['alert_type'])
            status_class = f"status-{alert['status']}"
            time_ago = format_time_ago(alert['created_at']) if isinstance(alert['created_at'], str) else "now"
            
            st.markdown(f"""
            <div class="alert-card">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <span class="status-badge {status_class}">{alert['status'].upper()}</span>
                        <strong style="color:{color}; margin-left:0.5rem;">#{alert['id']} {label}</strong>
                    </div>
                    <small style="color:#888;">{time_ago}</small>
                </div>
                <p style="margin:0.5rem 0; font-size:0.85rem;">
                    📍 {alert['latitude']:.5f}, {alert['longitude']:.5f}
                </p>
                <p style="margin:0; color:#aaa; font-size:0.8rem;">
                    {alert['description'][:60] + '...' if alert['description'] and len(alert['description']) > 60 else (alert['description'] or 'Pas de description')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if alert['status'] == 'active' and st.button("🚀 Prendre", key=f"take_{alert['id']}", use_container_width=True):
                    update_alert_status(alert['id'], 'in_progress', user['username'])
                    route = generate_route_points(center_lat, center_lon, alert['latitude'], alert['longitude'])
                    add_route_data(alert['id'], json.dumps(route), user['username'])
                    st.success("Intervention lancée!")
                    time.sleep(0.5)
                    st.rerun()
            with c2:
                if alert['status'] == 'in_progress' and st.button("✅ Résoudre", key=f"resolve_{alert['id']}", use_container_width=True):
                    update_alert_status(alert['id'], 'resolved', user['username'])
                    st.success("Alerte résolue!")
                    time.sleep(0.5)
                    st.rerun()
            with c3:
                if st.button("🗺 Itinéraire", key=f"route_{alert['id']}", use_container_width=True):
                    route = generate_route_points(center_lat, center_lon, alert['latitude'], alert['longitude'])
                    add_route_data(alert['id'], json.dumps(route), user['username'])
                    st.toast("Itinéraire calculé et affiché sur la carte")
                    st.rerun()

st.divider()
with st.expander("📜 Journal d'activité (Audit)"):
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
        st.info("Aucune activité enregistrée")

if st.button("← Retour à l'accueil", key="back_home_police2"):
    st.switch_page("streamlit_app.py")
