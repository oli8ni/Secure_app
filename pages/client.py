import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Alerte Urgence", page_icon="🚨", layout="centered")

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

from app.modules.database import init_db, create_alert
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

# ===============================
# GPS - LECTURE DES COORDONNEES
# ===============================
# Quand le JS recharge la page avec ?lat=X&lon=Y, on lit ici
query = st.query_params
has_gps_from_url = False

if "lat" in query and "lon" in query:
    try:
        lat_raw = query.get("lat")
        lon_raw = query.get("lon")
        # Streamlit peut retourner string ou liste
        if isinstance(lat_raw, list):
            lat_raw = lat_raw[0]
        if isinstance(lon_raw, list):
            lon_raw = lon_raw[0]
        parsed_lat = float(str(lat_raw))
        parsed_lon = float(str(lon_raw))
        if parsed_lat != 0.0 and parsed_lon != 0.0:
            st.session_state.gps_lat = parsed_lat
            st.session_state.gps_lon = parsed_lon
            st.session_state.gps_loaded = True
            has_gps_from_url = True
    except (ValueError, TypeError):
        pass

# Init session state
if "gps_lat" not in st.session_state:
    st.session_state.gps_lat = 0.0
if "gps_lon" not in st.session_state:
    st.session_state.gps_lon = 0.0
if "gps_loaded" not in st.session_state:
    st.session_state.gps_loaded = False
if "alert_sent" not in st.session_state:
    st.session_state.alert_sent = False
if "alert_id" not in st.session_state:
    st.session_state.alert_id = None

# Valeurs finales (session_state peut avoir ete mis a jour par le JS reload)
lat_input = st.session_state.gps_lat
lon_input = st.session_state.gps_lon

# ===============================
# STYLES
# ===============================
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
    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        14% { transform: scale(1.05); }
        28% { transform: scale(1); }
        42% { transform: scale(1.05); }
        70% { transform: scale(1); }
    }
    @keyframes scanline {
        0% { top: -5%; opacity: 0; }
        10% { opacity: 0.3; }
        90% { opacity: 0.3; }
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
        animation: scanline 4s linear infinite;
        z-index: 0;
        pointer-events: none;
    }
    .client-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #1a0a0a;
        margin-bottom: 1.5rem;
    }
    .client-header h1 {
        font-size: 2.2rem;
        font-weight: 900;
        color: #ff3333;
        text-transform: uppercase;
        letter-spacing: 6px;
        margin: 0;
        text-shadow: 0 0 20px rgba(255,0,0,0.4);
    }
    .client-header p {
        color: #555;
        font-size: 0.85rem;
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

# Geolocation - JS reloads page with ?lat=X&lon=Y query params
geo_html = """
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
    ">📍 Localiser ma position GPS</button>
    <div id="geo-status" style="margin-top:0.6rem; font-family:monospace; font-size:0.8rem;">
        <span style="color:#666">Cliquez pour obtenir vos coordonnees GPS</span>
    </div>
</div>
<script>
function getGPS() {
    const s = document.getElementById('geo-status');
    if (!navigator.geolocation) { s.innerHTML = '<span style="color:#ff4444">Geolocalisation non supportee</span>'; return; }
    s.innerHTML = '<span style="color:#4B8BFF"> Acquisition satellites... Patientez</span>';
    navigator.geolocation.getCurrentPosition(
        function(p) {
            var lat = p.coords.latitude.toFixed(6);
            var lon = p.coords.longitude.toFixed(6);
            var acc = Math.round(p.coords.accuracy);
            s.innerHTML = '<span style="color:#00ff88">✓ POSITION ACQUISE</span><br>' +
                '<span style="color:#aaa">LAT: ' + lat + ' | LON: ' + lon + ' | ACC: ±' + acc + 'm</span><br>' +
                '<span style="color:#4B8BFF; font-size:0.75rem;">Chargement...</span>';
            // Reload page with GPS coords in URL (Streamlit reads query_params on next load)
            var base = window.location.pathname;
            var params = new URLSearchParams(window.location.search);
            params.set('lat', lat);
            params.set('lon', lon);
            window.location.href = base + '?' + params.toString();
        },
        function(e) {
            var m='Erreur GPS. ';
            if(e.code==1) m+='Permission refusee.';
            else if(e.code==2) m+='Signal indisponible.';
            else if(e.code==3) m+='Delai depasse.';
            s.innerHTML = '<span style="color:#ff4444">' + m + '</span>';
        },
        {enableHighAccuracy:true, timeout:20000, maximumAge:0}
    );
}
</script>
"""
st.components.v1.html(geo_html, height=140)

# Affichage coords chargees
if st.session_state.gps_loaded and lat_input != 0.0 and lon_input != 0.0:
    st.success(f"✓ GPS charge : {lat_input:.6f}, {lon_input:.6f}")
else:
    st.info("📍 Cliquez sur 'Localiser ma position' ou saisissez manuellement")

# Saisie manuelle fallback
st.markdown("<p style='color:#444; font-size:0.7rem; text-align:center; margin:0.5rem 0;'>Saisie manuelle :</p>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    manual_lat = st.number_input("LATITUDE", value=lat_input, format="%.6f", step=0.000001, key="manual_lat")
with c2:
    manual_lon = st.number_input("LONGITUDE", value=lon_input, format="%.6f", step=0.000001, key="manual_lon")

# Sync manual input to session_state
if manual_lat != lat_input:
    st.session_state.gps_lat = manual_lat
    lat_input = manual_lat
if manual_lon != lon_input:
    st.session_state.gps_lon = manual_lon
    lon_input = manual_lon

# Display coords boxes
co1, co2, co3 = st.columns(3)
with co1:
    st.markdown(f'<div class="gps-box"><div class="gps-label">LATITUDE</div><div class="gps-coord">{lat_input:.6f}</div></div>', unsafe_allow_html=True)
with co2:
    st.markdown(f'<div class="gps-box"><div class="gps-label">LONGITUDE</div><div class="gps-coord">{lon_input:.6f}</div></div>', unsafe_allow_html=True)
with co3:
    is_valid = validate_coordinates(lat_input, lon_input)
    v_color = "#00ff88" if is_valid else "#ff4444"
    v_text = "VALIDE" if is_valid else "INVALIDE"
    st.markdown(f'<div class="gps-box"><div class="gps-label">STATUT GPS</div><div class="gps-coord" style="color:{v_color};">{v_text}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

# === DETAILS ===
st.markdown('<div class="section-label-blue">3. Details (optionnels)</div>', unsafe_allow_html=True)
desc = st.text_area("", placeholder="Decrivez la situation en cours...", height=70, key="desc_field", label_visibility="collapsed")
phone = st.text_input("Tel contact (optionnel)", placeholder="+225 XX XX XX XX", key="phone_field")

# === EMERGENCY BUTTON ===
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-label">4. Envoyer l\'alerte</div>', unsafe_allow_html=True)

has_valid = validate_coordinates(lat_input, lon_input)

# Visual rings
st.markdown("""
<div style="position:relative; width:260px; height:100px; margin:0 auto; display:flex; align-items:center; justify-content:center;">
    <div style="position:absolute; width:200px; height:200px; border-radius:50%; border:3px solid rgba(255,0,0,0.2); animation:pulse-ring 2.5s infinite;"></div>
    <div style="position:absolute; width:200px; height:200px; border-radius:50%; border:2px solid rgba(255,0,0,0.15); animation:pulse-ring2 2.5s infinite;"></div>
</div>
""", unsafe_allow_html=True)

if st.button("ALERTE\nURGENCE", key="big_red_btn", type="primary", disabled=not has_valid):
    if not has_valid:
        st.error("❌ Coordonnees invalides. Localisez-vous ou saisissez les coordonnees GPS.")
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
                st.session_state.alert_lat = lat_input
                st.session_state.alert_lon = lon_input
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

if not has_valid:
    st.warning("⚠️ Localisez-vous ou saisissez les coordonnees GPS avant d'envoyer.")

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
    
    # BOUTON: Voir le trajet de la police
    if st.button("🗺 VOIR LE TRAJET DE LA POLICE", type="secondary", use_container_width=True):
        st.switch_page("pages/trajet.py")
    
    if st.button("NOUVELLE ALERTE", type="secondary"):
        for key in ['alert_sent', 'alert_id', 'alert_lat', 'alert_lon', 'gps_lat', 'gps_lon', 'gps_loaded']:
            if key in st.session_state:
                if key in ['gps_lat', 'gps_lon']:
                    st.session_state[key] = 0.0
                elif key == 'gps_loaded':
                    st.session_state[key] = False
                elif key in ['alert_lat', 'alert_lon']:
                    st.session_state[key] = 0.0
                else:
                    st.session_state[key] = False if key == 'alert_sent' else None
        st.rerun()

st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

if st.button("← RETOUR ACCUEIL", key="back_home"):
    st.switch_page("streamlit_app.py")

st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves
</div>
""", unsafe_allow_html=True)
