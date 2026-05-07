import streamlit as st
import time
import requests
from datetime import datetime

st.set_page_config(
    page_title="MutuAlert - Alerte Urgence",
    page_icon="🚨",
    layout="centered",
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
from app.modules.database import init_db, create_alert, get_default_station
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

# ========================================
# GPS VIA STREAMLIT-GEOLOCATION (package)
# ========================================
try:
    from streamlit_geolocation import streamlit_geolocation
    GEOLOCATION_AVAILABLE = True
except ImportError:
    GEOLOCATION_AVAILABLE = False

# ========================================
# QUICK-SELECT POSITIONS RDC
# ========================================
RDC_POSITIONS = {
    "📍 Kinshasa - Gombe (Centre)": (-4.3010, 15.3130),
    "📍 Kinshasa - Gare Central": (-4.3250, 15.3222),
    "📍 Kinshasa - Kintambo": (-4.3340, 15.3100),
    "📍 Kinshasa - Limete": (-4.3700, 15.3500),
    "📍 Kinshasa - Bandal": (-4.3600, 15.2900),
    "📍 Kinshasa - Lemba": (-4.3950, 15.2800),
    "📍 Kinshasa - Matete": (-4.3850, 15.3400),
    "📍 Kinshasa - Ngaba": (-4.4100, 15.3100),
    "📍 Lubumbashi - Centre": (-11.6870, 27.5020),
    "📍 Goma - Centre": (-1.6580, 29.2200),
    "📍 Bukavu - Centre": (-2.5100, 28.8480),
    "📍 Kisangani - Centre": (0.5167, 25.2000),
    "📍 Mbuji-Mayi - Centre": (-6.1500, 23.6000),
    "📍 Kananga - Centre": (-5.5400, 22.2900),
    "📍 Kolwezi - Centre": (-10.7167, 25.4725),
    "📍 Matadi - Centre": (-5.8167, 13.4500),
    "📍 Likasi": (-10.9833, 26.7333),
    "📍 Uvira": (-3.4000, 29.1333),
    "📍 Butembo": (0.1500, 29.2833),
    "📍 Tshikapa": (-6.4167, 20.8000),
}

# ========================================
# SESSION STATE INITIALIZATION
# ========================================
def init_session_state():
    defaults = {
        "gps_lat": 0.0,
        "gps_lon": 0.0,
        "gps_loaded": False,
        "gps_source": "",
        "alert_sent": False,
        "alert_id": None,
        "alert_lat": 0.0,
        "alert_lon": 0.0,
        "geolocation_used": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# ========================================
# GPS STREAMLIT-GEOLOCATION (méthode principale)
# ========================================
def process_geolocation_result(loc_data):
    """Process streamlit-geolocation result dict."""
    if loc_data and isinstance(loc_data, dict):
        lat = loc_data.get("latitude")
        lon = loc_data.get("longitude")
        if lat and lon and abs(float(lat)) > 0.001:
            st.session_state.gps_lat = float(lat)
            st.session_state.gps_lon = float(lon)
            st.session_state.gps_loaded = True
            st.session_state.gps_source = f"gps ±{loc_data.get('accuracy', '?')}m"
            st.session_state.geolocation_used = True
            return True
    return False

# ========================================
# STYLES
# ========================================
st.markdown("""
<style>
    @keyframes heartbeat {
        0%,100%{transform:scale(1)} 14%{transform:scale(1.05)} 28%{transform:scale(1)} 42%{transform:scale(1.05)} 70%{transform:scale(1)}
    }
    @keyframes pulse-ring {
        0%{transform:scale(.85);opacity:1} 70%{transform:scale(1.5);opacity:0} 100%{transform:scale(1.5);opacity:0}
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes glow {
        0%,100%{box-shadow: 0 0 5px rgba(0,255,136,0.3)} 50%{box-shadow: 0 0 20px rgba(0,255,136,0.6)}
    }
    .ch {text-align:center; padding:1.5rem 0 1rem; border-bottom:2px solid #1a0a0a; margin-bottom:1.5rem}
    .ch h1 {font-size:2.2rem; font-weight:900; color:#f33; text-transform:uppercase; letter-spacing:6px; margin:0; text-shadow:0 0 20px rgba(255,0,0,.4)}
    .ch p {color:#555; font-size:.85rem; letter-spacing:3px; text-transform:uppercase; margin:.3rem 0 0}
    .sl {color:#f44; font-size:.7rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:.6rem; font-weight:bold}
    .slb {color:#4B8BFF; font-size:.7rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:.6rem; font-weight:bold}
    .gb {background:linear-gradient(145deg,#0d0d1a,#111122); border:1px solid #1a1a3a; border-radius:10px; padding:1rem; text-align:center}
    .gc {font-family:'Courier New',monospace; color:#0f8; font-size:1.1rem; font-weight:bold}
    .gl {color:#555; font-size:.7rem; text-transform:uppercase; letter-spacing:2px}
    .so {background:linear-gradient(135deg,#0a2a0a,#1a3a1a); border:1px solid #0f4; border-radius:10px; padding:1.2rem; margin:1rem 0; animation:slideIn .5s ease}
    .so h3 {color:#0f8; margin-top:0; font-size:1.1rem}
    .dr {display:flex; justify-content:space-between; padding:.4rem 0; border-bottom:1px solid #1a3a1a; font-size:.85rem}
    .dl {color:#888} .dv {color:#fff; font-weight:bold}
    .fc {text-align:center; color:#444; font-size:.75rem; margin-top:2rem; padding:1rem 0; border-top:1px solid #1a1a1a}
    .fc a {color:#4B8BFF; text-decoration:none}
    .gps-ok {color:#0f8; font-size:.9rem; font-weight:bold}
    .gps-warn {color:#f80; font-size:.85rem}
    .manual-box {background:linear-gradient(145deg,#1a1a2e,#0d0d1a); border:1px solid #333; border-radius:8px; padding:1rem; margin-top:.5rem}
    .geo-box {background:linear-gradient(145deg,#0a1a0a,#0d1a0d); border:1px solid #0f4; border-radius:10px; padding:1.2rem; margin:.5rem 0; animation:glow 3s infinite}
    .geo-title {color:#0f8; font-weight:bold; font-size:.9rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:.5rem}
    .rdc-grid {display:grid; grid-template-columns: repeat(2, 1fr); gap:.4rem; margin:.5rem 0}
    .rdc-position-btn {background:#1a1a2e; border:1px solid #333; border-radius:6px; padding:.4rem .6rem; font-size:.75rem; color:#ccc; cursor:pointer; text-align:left; transition:all .2s}
    .rdc-position-btn:hover {border-color:#4B8BFF; color:#fff; background:#1a1a3a}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="ch"><h1>🚨 MUTU ALERT</h1><p>Alerte d\'urgence - Envoyez votre position</p></div>', unsafe_allow_html=True)

# ========================================
# TYPE D'ALERTE
# ========================================
st.markdown('<div class="sl">1. Type d\'alerte</div>', unsafe_allow_html=True)

alert_type = st.segmented_control(
    "",
    ["danger", "medical", "fire", "suspicious", "other"],
    format_func=lambda x: {
        "danger": "🆘 DANGER",
        "medical": "🏥 MEDICAL",
        "fire": "🔥 INCENDIE",
        "suspicious": "👁 SUSPECT",
        "other": "⚠️ AUTRE",
    }.get(x, x),
    default="danger",
)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ========================================
# GPS LOCALISATION
# ========================================
st.markdown('<div class="slb">2. Localisation GPS</div>', unsafe_allow_html=True)

# ---- METHOD 0: streamlit-geolocation (le plus fiable sur Streamlit Cloud) ----
if GEOLOCATION_AVAILABLE:
    st.markdown("<div class='geo-box'>", unsafe_allow_html=True)
    st.markdown("<div class='geo-title'>📡 Géolocalisation GPS (Précise)</div>", unsafe_allow_html=True)
    st.caption("Cliquez puis autorisez l'accès à votre position dans le navigateur")

    loc_result = streamlit_geolocation()

    if loc_result and isinstance(loc_result, dict) and loc_result.get("latitude"):
        success = process_geolocation_result(loc_result)
        if success:
            st.success(f"✅ GPS: {st.session_state.gps_lat:.5f}, {st.session_state.gps_lon:.5f}")
            time.sleep(0.5)

    st.markdown("</div>", unsafe_allow_html=True)

# ---- METHOD 1: IP Geolocation côté serveur (toujours fonctionnel) ----
st.markdown("<div style='margin:.5rem 0'></div>", unsafe_allow_html=True)
if st.button("🌐 LOCALISER PAR IP (Serveur)", type="secondary", use_container_width=True):
    with st.spinner("Recherche de position via IP..."):
        location_found = False
        # Service 1: ipapi.co
        try:
            resp = requests.get("https://ipapi.co/json/", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("latitude") and data.get("longitude"):
                    st.session_state.gps_lat = float(data["latitude"])
                    st.session_state.gps_lon = float(data["longitude"])
                    st.session_state.gps_loaded = True
                    city = data.get("city", "inconnu")
                    country = data.get("country_name", "")
                    st.session_state.gps_source = f"IP: {city}, {country}"
                    location_found = True
                    st.success(f"✅ Position IP: {city}, {country}")
        except Exception:
            pass

        # Service 2: ipinfo.io
        if not location_found:
            try:
                resp = requests.get("https://ipinfo.io/json", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    loc = data.get("loc", "").split(",")
                    if len(loc) == 2:
                        st.session_state.gps_lat = float(loc[0])
                        st.session_state.gps_lon = float(loc[1])
                        st.session_state.gps_loaded = True
                        city = data.get("city", "inconnu")
                        st.session_state.gps_source = f"IP2: {city}"
                        location_found = True
                        st.success(f"✅ Position IP: {city}")
            except Exception:
                pass

        if not location_found:
            st.error("❌ Localisation IP impossible. Choisissez une position dans la liste ou saisissez manuellement.")

# ---- METHOD 2: Quick-Select Positions RDC ----
st.markdown("<div style='margin:.5rem 0'></div>", unsafe_allow_html=True)
with st.expander("📍 CHOISIR UNE POSITION PRÉDÉFINIE (RDC)", expanded=not st.session_state.gps_loaded):
    st.caption("Sélectionnez votre ville/quartier si le GPS ne fonctionne pas")

    # Afficher en grille 3 colonnes
    cols = st.columns(3)
    col_idx = 0
    for label, (lat, lon) in RDC_POSITIONS.items():
        with cols[col_idx % 3]:
            if st.button(label, key=f"rdc_{lat}_{lon}", use_container_width=True):
                st.session_state.gps_lat = lat
                st.session_state.gps_lon = lon
                st.session_state.gps_loaded = True
                st.session_state.gps_source = f"preset: {label}"
                st.rerun()
        col_idx += 1

# ---- METHOD 3: JavaScript GPS (mobile/direct) ----
with st.expander("📱 GPS NAVIGATEUR (Mobile/Direct)", expanded=False):
    st.caption("Fonctionne mieux sur mobile ou en accès direct (hors iframe Streamlit Cloud)")
    gps_html = """
    <div class="gb" id="gps-box">
        <button onclick="getGPS()" style="background:linear-gradient(135deg,#1a237e,#283593);color:white;border:none;padding:.8rem 1.5rem;border-radius:8px;font-size:.95rem;font-weight:bold;cursor:pointer;width:100%;letter-spacing:1px;text-transform:uppercase">
            📍 ACTIVER LE GPS
        </button>
        <div id="gps-out" style="margin-top:.8rem;font-family:monospace;font-size:.85rem;min-height:50px">
            <span style="color:#666">Cliquez pour obtenir vos coordonnees GPS</span>
        </div>
    </div>
    <script>
    function getGPS(){
        var out=document.getElementById('gps-out');
        out.innerHTML='<span style="color:#4B8BFF">▶ Acquisition GPS en cours...</span>';
        if(!navigator.geolocation){
            out.innerHTML='<span style="color:#f44">✗ Geolocalisation non supportee par ce navigateur.</span>';
            return;
        }
        navigator.geolocation.getCurrentPosition(
            function(pos){
                var lat=pos.coords.latitude.toFixed(6);
                var lon=pos.coords.longitude.toFixed(6);
                var acc=Math.round(pos.coords.accuracy);
                out.innerHTML='<div style="color:#0f8;font-weight:bold">✓ GPS OK</div><div style="color:#ccc">LAT: '+lat+' | LON: '+lon+'</div><div style="color:#888;font-size:.75rem">Precision: ±'+acc+'m</div><div style="color:#f80;font-size:.8rem;margin-top:.5px">⚠ Copiez ces coordonnees dans les champs manuels ci-dessous</div>';
            },
            function(err){
                var msg='Erreur: ';
                if(err.code==1)msg+='Permission refusee.';
                else if(err.code==2)msg+='Position indisponible.';
                else msg+='Delai depasse.';
                out.innerHTML='<span style="color:#f44">✗ '+msg+' Utilisez la localisation IP ou les positions predefinies.</span>';
            },
            {enableHighAccuracy:true,timeout:15000,maximumAge:0}
        );
    }
    </script>
    """
    st.components.v1.html(gps_html, height=180)

# ========================================
# GPS STATUS & RESET
# ========================================
lat_val = float(st.session_state.gps_lat)
lon_val = float(st.session_state.gps_lon)

c1, c2 = st.columns(2)
with c1:
    if st.session_state.gps_loaded and abs(lat_val) > 0.001:
        src_display = st.session_state.gps_source.upper()
        st.markdown(
            f'<div class="gps-ok">✓ Position chargee ({src_display})<br>'
            f'LAT: {lat_val:.6f} | LON: {lon_val:.6f}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="gps-warn">⚠ Aucune position. Choisissez une methode ci-dessus.</div>',
            unsafe_allow_html=True,
        )

with c2:
    if st.button("🔄 Reset / Rafraichir", use_container_width=True):
        st.session_state.gps_lat = 0.0
        st.session_state.gps_lon = 0.0
        st.session_state.gps_loaded = False
        st.session_state.gps_source = ""
        st.session_state.geolocation_used = False
        st.rerun()

# ========================================
# MANUAL ENTRY
# ========================================
st.markdown(
    "<div class='manual-box'><p style='color:#888;font-size:.8rem;margin:0 0 .5rem 0'>"
    "📝 Saisie manuelle (copiez les coordonnees GPS ici) :</p></div>",
    unsafe_allow_html=True,
)
c1, c2 = st.columns(2)
with c1:
    manual_lat = st.number_input("LATITUDE", value=lat_val, format="%.6f", step=0.000001, key="man_lat")
with c2:
    manual_lon = st.number_input("LONGITUDE", value=lon_val, format="%.6f", step=0.000001, key="man_lon")

if manual_lat != lat_val:
    st.session_state.gps_lat = manual_lat
    lat_val = manual_lat
if manual_lon != lon_val:
    st.session_state.gps_lon = manual_lon
    lon_val = manual_lon

# Display boxes
nc1, nc2, nc3 = st.columns(3)
with nc1:
    st.markdown(f'<div class="gb"><div class="gl">LAT</div><div class="gc">{lat_val:.6f}</div></div>', unsafe_allow_html=True)
with nc2:
    st.markdown(f'<div class="gb"><div class="gl">LON</div><div class="gc">{lon_val:.6f}</div></div>', unsafe_allow_html=True)
with nc3:
    is_v = validate_coordinates(lat_val, lon_val)
    v_c, v_t = ("#0f8", "VALIDE") if is_v else ("#f44", "INVALIDE")
    st.markdown(f'<div class="gb"><div class="gl">STATUT</div><div class="gc" style="color:{v_c}">{v_t}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ========================================
# DETAILS
# ========================================
st.markdown('<div class="slb">3. Details (optionnels)</div>', unsafe_allow_html=True)
desc = st.text_area("", placeholder="Decrivez la situation...", height=70, key="desc_field", label_visibility="collapsed")
phone = st.text_input("Tel contact (optionnel)", placeholder="+243 XX XXX XXXX", key="phone_field")

# ========================================
# EMERGENCY BUTTON
# ========================================
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="sl">4. Envoyer l\'alerte</div>', unsafe_allow_html=True)

has_valid = validate_coordinates(lat_val, lon_val)

st.markdown("""
<div style="position:relative;width:260px;height:80px;margin:0 auto;display:flex;align-items:center;justify-content:center">
    <div style="position:absolute;width:200px;height:200px;border-radius:50%;border:3px solid rgba(255,0,0,.2);animation:pulse-ring 2.5s infinite"></div>
    <div style="position:absolute;width:200px;height:200px;border-radius:50%;border:2px solid rgba(255,0,0,.15);animation:pulse-ring 3s infinite"></div>
</div>
""", unsafe_allow_html=True)

if st.button("ALERTE\nURGENCE", key="big_red_btn", type="primary", disabled=not has_valid):
    if not has_valid:
        st.error("❌ Coordonnees invalides. Choisissez une position ou saisissez les coordonnees.")
    else:
        with st.spinner("TRANSMISSION EN COURS..."):
            try:
                aid = create_alert(
                    alert_type=alert_type,
                    latitude=lat_val,
                    longitude=lon_val,
                    accuracy=50.0,
                    description=desc if desc else None,
                    phone=phone if phone else None,
                    device_id="web-" + str(hash(str(lat_val) + str(lon_val) + str(datetime.now())) % 100000),
                )
                st.session_state.alert_sent = True
                st.session_state.alert_id = aid
                st.session_state.alert_lat = lat_val
                st.session_state.alert_lon = lon_val
                time.sleep(1.5)
            except Exception as e:
                st.error(f"ERREUR TRANSMISSION: {str(e)}")

st.markdown("""
<style>
    [data-testid="stButton"]>button[kind="primary"]{
        width:200px!important;height:200px!important;border-radius:50%!important;
        background:radial-gradient(circle at 35% 35%,#f55,#c00,#800)!important;
        color:#fff!important;font-size:1.5rem!important;font-weight:900!important;
        border:3px solid #f88!important;box-shadow:0 0 30px rgba(255,0,0,.5),inset 0 0 40px rgba(0,0,0,.3)!important;
        animation:heartbeat 2s infinite!important;line-height:1.2!important;white-space:pre-line!important;
        display:block;margin:0 auto
    }
    [data-testid="stButton"]>button[kind="primary"]:hover{
        transform:scale(1.08)!important;background:radial-gradient(circle at 35% 35%,#f77,#d00,#a00)!important
    }
    [data-testid="stButton"]>button[kind="primary"]:disabled{
        background:#222!important;border-color:#444!important;color:#555!important;
        animation:none!important;box-shadow:none!important
    }
</style>
""", unsafe_allow_html=True)

if not has_valid:
    st.warning("⚠️ Choisissez une position GPS, une ville predefinie, ou saisissez manuellement.")

# ========================================
# SUCCESS
# ========================================
station = get_default_station()
station_name = station["name"] if station is not None else "Police"

if st.session_state.alert_sent:
    st.balloons()
    st.markdown(f"""
    <div class="so">
        <h3>✅ ALERTE #{st.session_state.alert_id} CONFIRMEE</h3>
        <div class="dr"><span class="dl">TYPE</span><span class="dv">{get_alert_label(alert_type)}</span></div>
        <div class="dr"><span class="dl">POSITION</span><span class="dv">{get_location_display(lat_val, lon_val)}</span></div>
        <div class="dr"><span class="dl">HEURE</span><span class="dv">{datetime.now().strftime('%H:%M:%S')}</span></div>
        <div class="dr"><span class="dl">POSTE POLICE</span><span class="dv" style="color:#4B8BFF">{station_name}</span></div>
        <div class="dr"><span class="dl">STATUT</span><span class="dv" style="color:#0f8">● ACTIVE - POLICE NOTIFIEE</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Restez calme. La police a recu votre position et est en route.")

    if st.button("🗺 VOIR LE TRAJET DE LA POLICE", type="secondary", use_container_width=True):
        st.switch_page("pages/trajet.py")

    if st.button("NOUVELLE ALERTE", type="secondary"):
        for k in ["alert_sent", "alert_id", "alert_lat", "alert_lon", "gps_lat", "gps_lon", "gps_loaded", "gps_source", "geolocation_used"]:
            if k in ("gps_lat", "gps_lon", "alert_lat", "alert_lon"):
                st.session_state[k] = 0.0
            elif k in ("alert_sent", "gps_loaded", "geolocation_used"):
                st.session_state[k] = False
            elif k == "gps_source":
                st.session_state[k] = ""
            else:
                st.session_state[k] = None
        st.rerun()

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
if st.button("← RETOUR ACCUEIL", key="back_home"):
    st.switch_page("streamlit_app.py")

st.markdown(
    f"""<div class="fc"><b>MutuAlert</b> &copy; 2026 | Powered by """
    f"""<a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves</div>""",
    unsafe_allow_html=True,
)
