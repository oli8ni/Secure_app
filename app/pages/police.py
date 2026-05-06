import pandas as pd
import streamlit as st
import folium
import json
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="MutuAlert - Centre de Commandement", page_icon="👮", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebarNav"]                 { display: none !important; }
    button[kind="header"]                        { display: none !important; }
    .stApp > header                              { display: none !important; }
    div[data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.modules.database import (
    init_db, get_all_alerts, update_alert_status, add_route_data,
    get_police_stations, get_default_station, add_police_station
)
from app.modules.auth import authenticate_user
from app.modules.geo import validate_coordinates, generate_route_points
from app.modules.alerts import get_alert_color, get_alert_label, format_time_ago
from streamlit_folium import st_folium

init_db()

st.markdown("""
<style>
    @keyframes blink-border { 0%,100%{border-color:rgba(255,0,0,.3)} 50%{border-color:rgba(255,0,0,.9)} }
    .cc-header   { background:linear-gradient(90deg,#0a0a1a,#1a1a3a 50%,#0a0a1a); border-bottom:2px solid #1a1a4a; padding:.8rem 1.2rem; margin:-1rem -1rem 1rem -1rem; display:flex; justify-content:space-between; align-items:center; }
    .cc-title    { font-size:1.3rem; font-weight:900; color:#4B8BFF; letter-spacing:3px; text-transform:uppercase; margin:0; }
    .cc-clock    { color:#0f8; font-family:monospace; font-size:1rem; font-weight:bold; }
    .cc-badge    { background:#f00; color:#fff; padding:2px 8px; border-radius:4px; font-size:.65rem; font-weight:bold; animation:blink-border 1.5s infinite; border:1px solid transparent; margin-left:.5rem; }
    .metric-panel{ background:linear-gradient(145deg,#0d0d1a,#141428); border:1px solid #1a1a3a; border-radius:8px; padding:.8rem; text-align:center; }
    .metric-num  { font-size:1.8rem; font-weight:900; line-height:1; }
    .metric-red  { color:#f00; text-shadow:0 0 15px rgba(255,0,0,.4); }
    .metric-amber{ color:#f80; }
    .metric-green{ color:#0f8; text-shadow:0 0 10px rgba(0,255,136,.3); }
    .metric-label{ font-size:.7rem; color:#666; text-transform:uppercase; letter-spacing:1px; margin-top:.3rem; }
    .alert-tile  { background:linear-gradient(145deg,#111122,#0a0a1a); border-left:3px solid #f00; border-radius:6px; padding:.8rem; margin-bottom:.5rem; transition:all .2s; }
    .alert-tile:hover          { background:#1a1a2e; transform:translateX(3px); }
    .alert-tile-resolved       { border-left-color:#0f8; }
    .alert-tile-progress       { border-left-color:#f80; }
    .tile-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:.3rem; }
    .tile-type   { font-size:.75rem; font-weight:bold; text-transform:uppercase; }
    .tile-time   { font-size:.7rem; color:#555; font-family:monospace; }
    .tile-coords { font-size:.75rem; color:#777; font-family:monospace; }
    .tile-desc   { font-size:.8rem; color:#999; margin-top:.3rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .login-box   { max-width:420px; margin:3rem auto; background:linear-gradient(145deg,#0a0a1a,#111122); border:1px solid #1a1a3a; border-radius:12px; padding:2rem; box-shadow:0 20px 60px rgba(0,0,0,.5); }
    .login-title { text-align:center; color:#4B8BFF; font-size:1.3rem; font-weight:900; letter-spacing:2px; margin-bottom:1.5rem; }
    .footer-co   { text-align:center; color:#444; font-size:.75rem; margin-top:2rem; padding:1rem 0; border-top:1px solid #1a1a1a; }
    .footer-co a { color:#4B8BFF; text-decoration:none; }
    .station-card  { background:linear-gradient(145deg,#0d0d1a,#141428); border:1px solid #1a1a3a; border-radius:8px; padding:.8rem; margin-bottom:.5rem; font-size:.8rem; }
    .station-active{ border-color:#0f8; }
    .demo-hint   { text-align:center; color:#555; font-size:.75rem; margin-top:.5rem; }
</style>
""", unsafe_allow_html=True)

if 'police_user' not in st.session_state:
    st.session_state.police_user = None

# =========================
# ÉCRAN DE CONNEXION
# ✅ FIX : champs vides par défaut — les credentials ne sont PLUS pré-remplis
#           visiblement. Un bouton "Mode Démo" reste disponible pour le jury.
# =========================
if st.session_state.police_user is None:
    st.markdown("""
    <div class="login-box">
        <div class="login-title">🔐 CENTRE DE COMMANDEMENT</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        username = st.text_input("IDENTIFIANT", placeholder="Entrez votre identifiant", key="login_user")
        password = st.text_input("MOT DE PASSE", type="password", placeholder="••••••••••", key="login_pass")

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("CONNEXION", type="primary", use_container_width=True):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.police_user = user
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")

        with btn2:
            # Bouton démo visible pour les jurés — mais sans afficher les credentials en clair
            if st.button("MODE DÉMO", use_container_width=True):
                user = authenticate_user("officer1", "Officer2026!")
                if user:
                    st.session_state.police_user = user
                    st.rerun()
                else:
                    st.error("Compte de démo non disponible")

        st.markdown(
            '<p class="demo-hint">Utilisez le bouton <b>Mode Démo</b> pour la démonstration</p>',
            unsafe_allow_html=True
        )

    if st.button("← RETOUR ACCUEIL"):
        st.switch_page("streamlit_app.py")
    st.stop()

user = st.session_state.police_user

# =========================
# HEADER
# =========================
st.markdown(f"""
<div class="cc-header">
    <div>
        <span class="cc-title">MUTU ALERT — COMMANDEMENT</span>
        <span class="cc-badge">LIVE</span>
    </div>
    <div class="cc-clock">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#0d0d1a,#141428);border-radius:8px;padding:1rem;margin-bottom:1rem;border:1px solid #1a1a3a">
        <div style="color:#4B8BFF;font-size:.7rem;text-transform:uppercase;letter-spacing:1px">Agent</div>
        <div style="color:#fff;font-weight:bold">{user['full_name']}</div>
        <div style="color:#888;font-size:.75rem">{user['role'].upper()}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 DÉCONNEXION", use_container_width=True):
        st.session_state.police_user = None
        st.rerun()

    st.divider()

    show_status = st.segmented_control(
        "", ["all", "active", "in_progress", "resolved"],
        format_func=lambda x: {
            "all":         "TOUS",
            "active":      "ACTIFS",
            "in_progress": "EN COURS",
            "resolved":    "RÉSOLUS"
        }.get(x, x),
        default="all"
    )

    st.divider()

    # ✅ Auto-refresh optionnel — le jury peut l'activer pour une démo live
    auto_refresh = st.checkbox("🔄 Rafraîchissement auto (10s)", value=False)

# =========================
# POSTES DE POLICE
# =========================
stations        = get_police_stations()
default_station = get_default_station()

with st.expander("🏢 Postes de Police"):
    st.subheader("Position du centre de police")

    if default_station is not None:
        st.success(f"Poste actif : **{default_station['name']}** ({default_station['latitude']:.5f}, {default_station['longitude']:.5f})")

    tab1, tab2 = st.tabs(["Liste des postes", "Ajouter un poste"])

    with tab1:
        for idx, station in stations.iterrows():
            active_badge = " 🟢 ACTIF" if station['is_default'] else ""
            st.markdown(f"""
            <div class="station-card{' station-active' if station['is_default'] else ''}">
                <b>#{station['id']} {station['name']}{active_badge}</b><br>
                📍 {station['latitude']:.5f}, {station['longitude']:.5f} | {station['address'] or 'N/A'}<br>
                📞 {station['phone'] or 'N/A'}
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if not station['is_default'] and st.button("Définir actif", key=f"setactive_{station['id']}", use_container_width=True):
                    from app.modules.database import update_station_default
                    update_station_default(station['id'])
                    st.rerun()
            with c2:
                if st.button("Supprimer", key=f"delstation_{station['id']}", use_container_width=True):
                    from app.modules.database import delete_station
                    delete_station(station['id'])
                    st.rerun()

    with tab2:
        st.markdown("**Nouveau poste de police**")
        s_name    = st.text_input("Nom",       key="s_name",    placeholder="Commissariat...")
        s_lat     = st.number_input("Latitude",  value=5.36,    format="%.6f", key="s_lat")
        s_lon     = st.number_input("Longitude", value=-4.0083, format="%.6f", key="s_lon")
        s_addr    = st.text_input("Adresse",   key="s_addr")
        s_phone   = st.text_input("Téléphone", key="s_phone")
        s_default = st.checkbox("Définir comme poste actif", value=False, key="s_default")
        if st.button("Ajouter le poste", type="primary"):
            add_police_station(s_name, s_lat, s_lon, s_addr, s_phone, s_default)
            st.rerun()

# =========================
# DONNÉES
# =========================
df_alerts = get_all_alerts(200)
if show_status != "all":
    df_alerts = df_alerts[df_alerts['status'] == show_status]

if 'zoom_to' not in st.session_state:
    st.session_state.zoom_to = None

# =========================
# MÉTRIQUES
# =========================
m1, m2, m3, m4 = st.columns(4)
ac = len(df_alerts[df_alerts['status'] == 'active'])
ip = len(df_alerts[df_alerts['status'] == 'in_progress'])
rc = len(df_alerts[df_alerts['status'] == 'resolved'])
tc = len(df_alerts)
with m1: st.markdown(f'<div class="metric-panel"><div class="metric-num metric-red">{ac}</div><div class="metric-label">Actives</div></div>',    unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-panel"><div class="metric-num metric-amber">{ip}</div><div class="metric-label">En Cours</div></div>',  unsafe_allow_html=True)
with m3: st.markdown(f'<div class="metric-panel"><div class="metric-num metric-green">{rc}</div><div class="metric-label">Résolues</div></div>',  unsafe_allow_html=True)
with m4: st.markdown(f'<div class="metric-panel"><div class="metric-num" style="color:#4B8BFF">{tc}</div><div class="metric-label">Total</div></div>', unsafe_allow_html=True)

st.divider()
left, right = st.columns([3, 2])

# =========================
# CARTE TEMPS RÉEL
# =========================
with left:
    st.markdown("<div style='color:#888;font-size:.75rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:.5rem'>🗺 Carte Temps Réel</div>", unsafe_allow_html=True)

    police_lat = default_station['latitude']  if default_station is not None else 5.36
    police_lon = default_station['longitude'] if default_station is not None else -4.0083

    if st.session_state.zoom_to and len(df_alerts) > 0:
        za = df_alerts[df_alerts['id'] == st.session_state.zoom_to]
        if len(za) > 0:
            center_lat  = za.iloc[0]['latitude']
            center_lon  = za.iloc[0]['longitude']
            zoom_level  = 16
        else:
            center_lat, center_lon, zoom_level = police_lat, police_lon, 13
    else:
        center_lat, center_lon, zoom_level = police_lat, police_lon, 13

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, tiles="CartoDB dark_matter")

    # Poste de police
    folium.Marker(
        [police_lat, police_lon],
        icon=folium.Icon(color='darkblue', icon='shield', prefix='fa'),
        popup=f"<b>{default_station['name'] if default_station is not None else 'Police'}</b>",
        tooltip="🚔 POSTE DE POLICE"
    ).add_to(m)
    folium.Circle(
        [police_lat, police_lon], radius=500,
        fill=True, color='#4B8BFF', fill_color='#4B8BFF', fill_opacity=0.05
    ).add_to(m)

    for idx, alert in df_alerts.iterrows():
        color    = get_alert_color(alert['alert_type'])
        label    = get_alert_label(alert['alert_type'])
        status   = alert['status']
        lat, lon = alert['latitude'], alert['longitude']
        is_zoomed = st.session_state.zoom_to == alert['id']

        if status == 'active':
            folium.CircleMarker([lat, lon], radius=8, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.6).add_to(m)
            folium.Circle([lat, lon], radius=80, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.12 if not is_zoomed else 0.25).add_to(m)
            folium.Circle([lat, lon], radius=200, fill=True, color='#FF0000', fill_color='#FF0000', fill_opacity=0.04).add_to(m)
            popup_html = f"""
            <div style="font-family:sans-serif;min-width:200px;color:#fff;background:#111;padding:10px;border-radius:6px;border-left:3px solid {color}">
                <h4 style="color:{color};margin:0;font-size:1rem">🚨 {label} #{alert['id']}</h4>
                <hr style="border-color:#333;margin:6px 0">
                <p style="margin:4px 0;font-size:.8rem"><b style="color:#fff">Statut :</b> <span style="color:#f00;font-weight:bold">ACTIVE</span></p>
                <p style="margin:4px 0;font-size:.8rem"><b style="color:#fff">Heure :</b> {alert['created_at']}</p>
                <p style="margin:4px 0;font-size:.8rem"><b style="color:#fff">Desc. :</b> {str(alert['description']) if alert['description'] else 'N/A'}</p>
                <p style="margin:4px 0;font-size:.8rem"><b style="color:#fff">Tél. :</b> {alert['phone'] or 'Anonyme'}</p>
            </div>"""
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color='red', icon='exclamation', prefix='fa'),
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"🔴 #{alert['id']} {label}"
            ).add_to(m)

        elif status == 'in_progress':
            folium.Marker([lat, lon], icon=folium.Icon(color='orange', icon='car', prefix='fa'), tooltip=f"🟡 #{alert['id']} En cours").add_to(m)
            if alert['route_data']:
                try:
                    route = json.loads(alert['route_data'])
                    if isinstance(route, list) and len(route) > 1:
                        folium.PolyLine(route, color='#FF8800', weight=5, opacity=0.9).add_to(m)
                except Exception:
                    pass
        else:
            folium.Marker([lat, lon], icon=folium.Icon(color='green', icon='check', prefix='fa'), tooltip=f"🟢 #{alert['id']} Résolu").add_to(m)

    # Itinéraires en pointillés pour alertes actives
    for idx, alert in df_alerts[df_alerts['status'] == 'active'].iterrows():
        route_pts = generate_route_points(police_lat, police_lon, alert['latitude'], alert['longitude'], num_points=20)
        folium.PolyLine(route_pts, color='#FF0000', weight=2, opacity=0.4, dash_array='5,10').add_to(m)

    st_folium(m, width=700, height=550, returned_objects=[])

# =========================
# LISTE ALERTES
# =========================
with right:
    st.markdown("<div style='color:#888;font-size:.75rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:.5rem'>📋 Alertes</div>", unsafe_allow_html=True)

    if len(df_alerts) == 0:
        st.info("Aucune alerte.")
    else:
        for idx, alert in df_alerts.head(15).iterrows():
            color      = get_alert_color(alert['alert_type'])
            label      = get_alert_label(alert['alert_type'])
            tile_class = (
                "alert-tile alert-tile-resolved" if alert['status'] == 'resolved' else
                "alert-tile alert-tile-progress" if alert['status'] == 'in_progress' else
                "alert-tile"
            )
            time_ago = format_time_ago(alert['created_at']) if isinstance(alert['created_at'], str) else "now"
            desc = str(alert['description'])
            if desc in ('None', ''):
                desc = 'Pas de description'
            elif len(desc) > 50:
                desc = desc[:50] + '...'

            st.markdown(f"""
            <div class="{tile_class}">
                <div class="tile-header">
                    <span class="tile-type" style="color:{color}">#{alert['id']} {label}</span>
                    <span class="tile-time">{time_ago}</span>
                </div>
                <div class="tile-coords">📍 {alert['latitude']:.5f}, {alert['longitude']:.5f}</div>
                <div class="tile-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("🔍 ZOOM",    key=f"zoom_{alert['id']}",    use_container_width=True):
                    st.session_state.zoom_to = alert['id']
                    st.rerun()
            with c2:
                if alert['status'] == 'active' and st.button("🚀 PRENDRE", key=f"take_{alert['id']}", use_container_width=True):
                    route = generate_route_points(police_lat, police_lon, alert['latitude'], alert['longitude'])
                    add_route_data(alert['id'], json.dumps(route), user['username'])
                    update_alert_status(alert['id'], 'in_progress', user['username'])
                    st.toast("Intervention lancée !")
                    time.sleep(.3)
                    st.rerun()
            with c3:
                if alert['status'] == 'in_progress' and st.button("✅ RÉSOUDRE", key=f"resolve_{alert['id']}", use_container_width=True):
                    update_alert_status(alert['id'], 'resolved', user['username'])
                    st.toast("Résolu !")
                    time.sleep(.3)
                    st.rerun()
            with c4:
                if st.button("🗺 ROUTE", key=f"route_{alert['id']}", use_container_width=True):
                    route = generate_route_points(police_lat, police_lon, alert['latitude'], alert['longitude'])
                    add_route_data(alert['id'], json.dumps(route), user['username'])
                    st.toast("Route calculée")
                    st.rerun()

# =========================
# JOURNAL D'ACTIVITÉ
# =========================
st.divider()
with st.expander("📜 JOURNAL D'ACTIVITÉ"):
    from app.modules.database import get_db
    with get_db() as conn:
        logs = pd.read_sql_query(
            "SELECT al.*, a.latitude, a.longitude FROM alert_logs al JOIN alerts a ON al.alert_id=a.id ORDER BY al.timestamp DESC LIMIT 50",
            conn
        )
    if len(logs) > 0:
        st.dataframe(logs[['timestamp', 'alert_id', 'action', 'performed_by']], use_container_width=True, hide_index=True)
    else:
        st.info("Aucune activité")

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
if st.button("← RETOUR ACCUEIL"):
    st.switch_page("streamlit_app.py")

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&amp;O Itech Solution</a> | Tous droits réservés
</div>
""", unsafe_allow_html=True)

# ✅ Auto-refresh en fin de script (après tout le rendu)
if auto_refresh:
    time.sleep(10)
    st.rerun()
