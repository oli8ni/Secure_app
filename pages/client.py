import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Alerte Urgence", page_icon="🚨", layout="centered")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import init_db, create_alert
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

# Read GPS from query params (set by JavaScript geolocation)
query_params = st.query_params
qp_lat = float(query_params.get("lat", 0.0)) if query_params.get("lat") else 0.0
qp_lon = float(query_params.get("lon", 0.0)) if query_params.get("lon") else 0.0

st.markdown("""
<style>
    @keyframes pulse-ring {
        0% { transform: scale(0.85); opacity: 1; }
        70% { transform: scale(1.5); opacity: 0; }
        100% { transform: scale(1.5); opacity: 0; }
    }
    @keyframes pulse-ring2 {
        0% { transform: scale(0.9); opacity: 0.6; }
        70% { transform: scale(1.6); opacity: 0; }
        100% { transform: scale(1.6); opacity: 0; }
    }
    @keyframes pulse-btn {
        0% { box-shadow: 0 0 0 0 rgba(255,0,0,0.7), inset 0 0 30px rgba(255,0,0,0.3); }
        50% { box-shadow: 0 0 0 25px rgba(255,0,0,0), inset 0 0 50px rgba(255,0,0,0.5); }
        100% { box-shadow: 0 0 0 0 rgba(255,0,0,0), inset 0 0 30px rgba(255,0,0,0.3); }
    }
    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        14% { transform: scale(1.05); }
        28% { transform: scale(1); }
        42% { transform: scale(1.05); }
        70% { transform: scale(1); }
    }
    @keyframes scan-down {
        0% { top: -5%; opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { top: 105%; opacity: 0; }
    }
    .client-bg {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 50% 0%, #1a0808 0%, #0a0a0a 50%, #000 100%);
        z-index: -1;
    }
    .scan-line {
        position: fixed;
        left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,75,75,0.3), transparent);
        animation: scan-down 4s linear infinite;
        z-index: 0;
        pointer-events: none;
    }
    .client-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #222;
        margin-bottom: 1rem;
    }
    .client-header h1 {
        font-size: 1.8rem;
        font-weight: 900;
        color: #ff3333;
        text-transform: uppercase;
        letter-spacing: 6px;
        margin: 0;
        text-shadow: 0 0 15px rgba(255,0,0,0.4);
    }
    .client-header p {
        color: #555;
        font-size: 0.8rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0.3rem 0 0 0;
    }
    .section-label {
        color: #FF4B4B;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0.6rem;
        font-weight: bold;
    }
    .section-label-blue {
        color: #4B8BFF;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0.6rem;
        font-weight: bold;
    }
    .gps-box {
        background: linear-gradient(145deg, #0d0d1a, #111122);
        border: 1px solid #1a1a3a;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .gps-coord {
        font-family: 'Courier New', monospace;
        color: #00ff88;
        font-size: 1.1rem;
        font-weight: bold;
    }
    .gps-label {
        color: #555;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .status-ok {
        background: linear-gradient(135deg, #0a2a0a 0%, #1a3a1a 100%);
        border: 1px solid #00ff44;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    .status-ok h3 {
        color: #00ff44;
        margin-top: 0;
        font-size: 1.1rem;
    }
    .data-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid #1a3a1a;
        font-size: 0.85rem;
    }
    .data-label { color: #888; }
    .data-value { color: #fff; font-weight: bold; }
    .emergency-btn-container {
        position: relative;
        width: 240px;
        height: 240px;
        margin: 1.5rem auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .ring1 {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 3px solid rgba(255,0,0,0.25);
        animation: pulse-ring 2.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }
    .ring2 {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid rgba(255,0,0,0.15);
        animation: pulse-ring2 2.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
        animation-delay: 0.6s;
    }
    .footer-co {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #0a0a0a;
        border-top: 1px solid #1a1a1a;
        padding: 0.5rem 1rem;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 100;
        font-size: 0.7rem;
        color: #555;
    }
    .footer-co a { color: #555; text-decoration: none; }
    .footer-co a:hover { color: #FF4B4B; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="client-bg"></div>', unsafe_allow_html=True)
st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="client-header">
    <h1>🚨 MUTU ALERT</h1>
    <p>Alerte d'urgence - Envoyez votre position</p>
</div>
""", unsafe_allow_html=True)

# === TYPE D'ALERTE ===
st.markdown('<div class="section-label">1. Type d\'alerte</div>', unsafe_allow_html=True)
alert_type = st.segmented_control(
    "", ["danger", "medical", "fire", "suspicious", "other"],
    format_func=lambda x: {"danger":"🆘 DANGER", "medical":"🏥 MEDICAL", "fire":"🔥 INCENDIE", "suspicious":"👁 SUSPECT", "other":"⚠️ AUTRE"}.get(x, x),
    default="danger"
)

st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

# === GPS LOCALISATION ===
st.markdown('<div class="section-label-blue">2. Localisation GPS</div>', unsafe_allow_html=True)

# Geolocation button that reloads page with coords in URL
geo_html = f"""
<div class="gps-box">
    <button onclick="getGPS()" style="
        background: linear-gradient(135deg, #1a237e, #283593);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-size: 0.95rem;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        letter-spacing: 1px;
        text-transform: uppercase;
    ">📍 Localiser ma position</button>
    <div id="geo-status" style="margin-top:0.6rem; font-family:monospace; font-size:0.8rem; color:#888;">
        Cliquez pour obtenir vos coordonnees GPS
    </div>
</div>
<script>
function getGPS() {{
    const s = document.getElementById('geo-status');
    if (!navigator.geolocation) {{ s.innerHTML = '<span style="color:#ff4444">Geolocalisation non supportee</span>'; return; }}
    s.innerHTML = '<span style="color:#4B8BFF"> Acquisition satellites...</span>';
    navigator.geolocation.getCurrentPosition(
        function(p) {{
            const lat = p.coords.latitude.toFixed(6);
            const lon = p.coords.longitude.toFixed(6);
            const acc = Math.round(p.coords.accuracy);
            s.innerHTML = '<span style="color:#00ff88">✓ POSITION ACQUISE</span><br>' +
                '<span style="color:#aaa">LAT: ' + lat + ' | LON: ' + lon + ' | ACC: ±' + acc + 'm</span><br>' +
                '<span style="color:#4B8BFF; font-size:0.75rem;">Rechargement de la page...</span>';
            setTimeout(function() {{
                const url = new URL(window.location.href);
                url.searchParams.set('lat', lat);
                url.searchParams.set('lon', lon);
                window.location.href = url.toString();
            }}, 800);
        }},
        function(e) {{
            let m='Erreur GPS. ';
            if(e.code==1) m+='Permission refusee.';
            else if(e.code==2) m+='Signal indisponible.';
            else if(e.code==3) m+='Delai depasse.';
            s.innerHTML = '<span style="color:#ff4444">' + m + '</span>';
        }},
        {{enableHighAccuracy:true, timeout:15000, maximumAge:0}}
    );
}}
// Auto-fill display
const url = new URL(window.location.href);
if (url.searchParams.has('lat') && url.searchParams.has('lon')) {{
    document.getElementById('geo-status').innerHTML = 
        '<span style="color:#00ff88">✓ POSITION CHARGEE</span><br>' +
        '<span style="color:#aaa">LAT: ' + url.searchParams.get('lat') + ' | LON: ' + url.searchParams.get('lon') + '</span>';
}}
</script>
"""
st.components.v1.html(geo_html, height=140)

# Manual coords - pre-filled from query params
st.markdown("<p style='color:#444; font-size:0.7rem; text-align:center; margin:0.5rem 0;'>Ou saisissez manuellement :</p>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    lat_input = st.number_input("LATITUDE", value=qp_lat, format="%.6f", step=0.000001, key="man_lat")
with c2:
    lon_input = st.number_input("LONGITUDE", value=qp_lon, format="%.6f", step=0.000001, key="man_lon")

# Show coords status
co1, co2, co3 = st.columns(3)
with co1:
    st.markdown(f'<div class="gps-box"><div class="gps-label">LATITUDE</div><div class="gps-coord">{lat_input:.6f}</div></div>', unsafe_allow_html=True)
with co2:
    st.markdown(f'<div class="gps-box"><div class="gps-label">LONGITUDE</div><div class="gps-coord">{lon_input:.6f}</div></div>', unsafe_allow_html=True)
with co3:
    valid_str = "VALIDE" if validate_coordinates(lat_input, lon_input) else "INVALIDE"
    valid_color = "#00ff88" if validate_coordinates(lat_input, lon_input) else "#ff4444"
    st.markdown(f'<div class="gps-box"><div class="gps-label">STATUT</div><div class="gps-coord" style="color:{valid_color};">{valid_str}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

# === DETAILS ===
st.markdown('<div class="section-label-blue">3. Details (optionnels)</div>', unsafe_allow_html=True)
desc = st.text_area("", placeholder="Decrivez la situation en cours...", height=70, key="desc_field", label_visibility="collapsed")
phone = st.text_input("Tel contact (optionnel)", placeholder="+225 XX XX XX XX", key="phone_field")

# Session state
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False
if 'alert_id' not in st.session_state:
    st.session_state.alert_id = None

has_valid = validate_coordinates(lat_input, lon_input)

# === EMERGENCY BUTTON ===
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-label">4. Envoyer l\'alerte</div>', unsafe_allow_html=True)

if st.button("ALERTE\nURGENCE", key="big_red_btn", type="primary", use_container_width=False, disabled=not has_valid):
    if not has_valid:
        st.error("Coordonnees invalides. Localisez-vous ou saisissez les coordonnees.")
    else:
        with st.spinner("TRANSMISSION EN COURS..."):
            try:
                aid = create_alert(
                    alert_type=alert_type,
                    latitude=lat_input,
                    longitude=lon_input,
                    accuracy=50.0,
                    description=desc if desc else None,
                    phone=phone if phone else None,
                    device_id=st.session_state.get('dev_id', 'web-' + str(hash(str(lat_input)) % 100000))
                )
                st.session_state.alert_sent = True
                st.session_state.alert_id = aid
                time.sleep(1.5)
            except Exception as e:
                st.error(f"ERREUR TRANSMISSION: {str(e)}")

st.markdown("""
<style>
    [data-testid="stButton"] > button[kind="primary"] {
        width: 200px !important;
        height: 200px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 35% 35%, #ff5555, #cc0000, #880000) !important;
        color: white !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        border: 3px solid #ff8888 !important;
        box-shadow: 0 0 30px rgba(255,0,0,0.5), inset 0 0 40px rgba(0,0,0,0.3) !important;
        animation: heartbeat 2s infinite !important;
        line-height: 1.2 !important;
        white-space: pre-line !important;
        display: block;
        margin: 0 auto;
    }
    [data-testid="stButton"] > button[kind="primary"]:hover {
        transform: scale(1.08) !important;
        background: radial-gradient(circle at 35% 35%, #ff7777, #dd0000, #aa0000) !important;
    }
    [data-testid="stButton"] > button[kind="primary"]:disabled {
        background: #222 !important;
        border-color: #444 !important;
        color: #555 !important;
        animation: none !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }
</style>
""", unsafe_allow_html=True)

# Visual rings around button
st.markdown("""
<div class="emergency-btn-container">
    <div class="ring1"></div>
    <div class="ring2"></div>
</div>
""", unsafe_allow_html=True)

if not has_valid:
    st.warning("⚠️ Localisez votre position ou saisissez les coordonnees GPS avant d'envoyer.")

# === SUCCESS ===
if st.session_state.alert_sent:
    st.balloons()
    st.markdown(f"""
    <div class="status-ok">
        <h3>✅ ALERTE #{st.session_state.alert_id} CONFIRMEE</h3>
        <div class="data-row"><span class="data-label">TYPE</span><span class="data-value">{get_alert_label(alert_type)}</span></div>
        <div class="data-row"><span class="data-label">POSITION</span><span class="data-value">{get_location_display(lat_input, lon_input)}</span></div>
        <div class="data-row"><span class="data-label">HEURE</span><span class="data-value">{datetime.now().strftime('%H:%M:%S')}</span></div>
        <div class="data-row"><span class="data-label">STATUT</span><span class="data-value" style="color:#00ff44;">● ACTIVE - POLICE NOTIFIEE</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Restez calme. Trouvez un endroit sur. Gardez votre telephone allume. La police a recu votre position exacte.")
    if st.button("NOUVELLE ALERTE", type="secondary"):
        st.session_state.alert_sent = False
        st.session_state.alert_id = None
        # Clear query params
        st.query_params.clear()
        st.rerun()

st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

if st.button("← RETOUR ACCUEIL", key="back_home"):
    st.switch_page("streamlit_app.py")

# Footer
st.markdown("""
<div class="footer-co">
    Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> &copy; 2026 - Tous droits reserves
</div>
""", unsafe_allow_html=True)
