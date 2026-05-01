import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="ALERTE URGENCE", page_icon="🚨", layout="centered")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import init_db, create_alert
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

st.markdown("""
<style>
    @keyframes pulse-ring {
        0% { transform: scale(0.8); opacity: 1; }
        80% { transform: scale(1.4); opacity: 0; }
        100% { transform: scale(1.4); opacity: 0; }
    }
    @keyframes pulse-btn {
        0% { box-shadow: 0 0 0 0 rgba(255,0,0,0.7), 0 0 20px rgba(255,0,0,0.4) inset; }
        50% { box-shadow: 0 0 0 30px rgba(255,0,0,0), 0 0 60px rgba(255,0,0,0.6) inset; }
        100% { box-shadow: 0 0 0 0 rgba(255,0,0,0), 0 0 20px rgba(255,0,0,0.4) inset; }
    }
    @keyframes shake {
        0%,100% { transform: translateX(0); }
        10%,30%,50%,70%,90% { transform: translateX(-2px); }
        20%,40%,60%,80% { transform: translateX(2px); }
    }
    @keyframes scanline {
        0% { top: -10%; }
        100% { top: 110%; }
    }
    .urgency-bg {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at center, #1a0a0a 0%, #0d0d0d 60%, #000000 100%);
        z-index: -1;
    }
    .urgency-header {
        text-align: center;
        margin-bottom: 1rem;
    }
    .urgency-header h1 {
        font-size: 2rem;
        font-weight: 900;
        color: #ff0000;
        text-transform: uppercase;
        letter-spacing: 4px;
        text-shadow: 0 0 20px rgba(255,0,0,0.5);
        margin: 0;
    }
    .urgency-header p {
        color: #666;
        font-size: 0.9rem;
        letter-spacing: 2px;
        margin: 0.3rem 0 0 0;
    }
    .emergency-ring {
        position: relative;
        width: 280px;
        height: 280px;
        margin: 1rem auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .emergency-ring::before {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 3px solid rgba(255,0,0,0.3);
        animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }
    .emergency-ring::after {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 3px solid rgba(255,0,0,0.2);
        animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
        animation-delay: 0.5s;
    }
    .status-ok {
        background: linear-gradient(135deg, #0a2a0a 0%, #1a3a1a 100%);
        border-left: 4px solid #00ff44;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .status-ok h3 {
        color: #00ff44;
        margin-top: 0;
    }
    .data-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid #222;
        font-size: 0.9rem;
    }
    .data-label { color: #888; }
    .data-value { color: #fff; font-weight: bold; }
    .type-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .type-btn {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 0.6rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        color: #aaa;
        font-size: 0.85rem;
    }
    .type-btn:hover { border-color: #FF4B4B; color: #fff; }
    .type-btn.active { border-color: #FF4B4B; background: rgba(255,75,75,0.1); color: #FF4B4B; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="urgency-bg"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="urgency-header">
    <h1>🚨 ALERTE D'URGENCE</h1>
    <p>Envoyez votre position aux forces de l'ordre</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Alert type selector
st.markdown("<p style='color:#888; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:0.5rem;'>Type d'alerte</p>", unsafe_allow_html=True)

alert_type = st.segmented_control(
    "",
    options=["danger", "medical", "fire", "suspicious", "other"],
    format_func=lambda x: {
        "danger": "🆘 DANGER",
        "medical": "🏥 MEDICAL",
        "fire": "🔥 INCENDIE",
        "suspicious": "👁 SUSPECT",
        "other": "⚠️ AUTRE"
    }.get(x, x),
    default="danger"
)

st.divider()

# GPS Location
st.markdown("<p style='color:#888; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:0.5rem;'>Localisation GPS</p>", unsafe_allow_html=True)

geo_html = """
<div style="text-align:center; margin-bottom:1rem;">
    <button onclick="getLoc()" style="
        background: linear-gradient(135deg, #1a237e, #283593);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        cursor: pointer;
        width: 100%;
    ">📍 LOCALISER MA POSITION</button>
    <div id="geo-res" style="
        background: #0d0d1a;
        border: 1px solid #1a237e;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
        display: none;
        font-family: monospace;
        text-align: left;
    "></div>
</div>
<script>
function getLoc() {
    const r = document.getElementById('geo-res');
    if (!navigator.geolocation) { r.style.display='block'; r.innerHTML='<span style="color:#ff4444">Geolocalisation non supportee</span>'; return; }
    r.style.display='block';
    r.innerHTML='<span style="color:#888">Acquisition satellites...</span>';
    navigator.geolocation.getCurrentPosition(
        function(p) {
            r.innerHTML = '<span style="color:#00ff88">✓ POSITION VERIFIEE</span><br>' +
                '<span style="color:#aaa">LAT: ' + p.coords.latitude.toFixed(6) + '</span><br>' +
                '<span style="color:#aaa">LON: ' + p.coords.longitude.toFixed(6) + '</span><br>' +
                '<span style="color:#aaa">ACC: ±' + Math.round(p.coords.accuracy) + 'm</span>';
            window.parent.postMessage({type:'streamlit:setComponentValue',value:{lat:p.coords.latitude,lon:p.coords.longitude}},'*');
        },
        function(e) {
            let m='Erreur GPS. ';
            if(e.code==1)m+='Permission refusee.';
            else if(e.code==2)m+='Signal indisponible.';
            else if(e.code==3)m+='Delai depasse.';
            r.innerHTML='<span style="color:#ff4444">'+m+'</span>';
        },
        {enableHighAccuracy:true, timeout:12000, maximumAge:0}
    );
}
</script>
"""
st.components.v1.html(geo_html, height=200)

st.markdown("<p style='color:#555; font-size:0.75rem; text-align:center;'>Ou saisissez manuellement :</p>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    lat_input = st.number_input("LATITUDE", value=0.0, format="%.6f", step=0.000001, key="man_lat", label_visibility="collapsed")
with c2:
    lon_input = st.number_input("LONGITUDE", value=0.0, format="%.6f", step=0.000001, key="man_lon", label_visibility="collapsed")

st.divider()

# Optional details
st.markdown("<p style='color:#888; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:0.5rem;'>Details (optionnels)</p>", unsafe_allow_html=True)
desc = st.text_area("", placeholder="Decrivez la situation en cours...", height=80, key="desc_field", label_visibility="collapsed")
phone = st.text_input("Tel contact (optionnel)", placeholder="+225 XX XX XX XX", key="phone_field")

st.divider()

# Session state
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False
if 'alert_id' not in st.session_state:
    st.session_state.alert_id = None

has_valid = validate_coordinates(lat_input, lon_input)

# EMERGENCY BUTTON
st.markdown("<div class='emergency-ring'>", unsafe_allow_html=True)
btn_disabled = not has_valid

if st.button("ALERTE\nURGENCE", key="big_red_btn", type="primary", use_container_width=False, disabled=btn_disabled):
    if not has_valid:
        st.error("Coordonnees invalides")
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

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid="stButton"] > button[kind="primary"] {
        width: 220px !important;
        height: 220px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 35% 35%, #ff5555, #cc0000, #880000) !important;
        color: white !important;
        font-size: 1.6rem !important;
        font-weight: 900 !important;
        border: 3px solid #ff8888 !important;
        box-shadow: 0 0 30px rgba(255,0,0,0.5), inset 0 0 40px rgba(0,0,0,0.3) !important;
        animation: pulse-btn 2s infinite !important;
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
        background: #333 !important;
        border-color: #555 !important;
        color: #666 !important;
        animation: none !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }
</style>
""", unsafe_allow_html=True)

if not has_valid and (lat_input == 0.0 and lon_input == 0.0):
    st.warning("⚠️ Localisez votre position ou saisissez les coordonnees avant d'envoyer.")

# Success display
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
    
    st.info("""
    **Consignes de securite:**
    Restez calme. Trouvez un endroit sur. Gardez votre telephone allume. La police a recu votre position exacte. En cas de danger imminent, contactez directement les urgences locales.
    """)
    
    if st.button("NOUVELLE ALERTE", type="secondary"):
        st.session_state.alert_sent = False
        st.session_state.alert_id = None
        st.rerun()

st.divider()
if st.button("← RETOUR ACCUEIL", key="back_home"):
    st.switch_page("streamlit_app.py")
