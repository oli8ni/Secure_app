import streamlit as st
import time
import requests
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Alerte Urgence", page_icon="🚨", layout="centered", initial_sidebar_state="collapsed")

# === HIDE SIDEBAR NAVIGATION COMPLETELY ===
hide_sidebar_css = """
<style>
    /* Hide sidebar navigation */
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    /* Hide hamburger menu */
    .stApp > header {display: none !important;}
    /* Remove top padding */
    .reportview-container .main .block-container {padding-top: 0 !important;}
    /* Hide sidebar collapse control */
    [data-testid="stSidebarCollapsedControl"] {display: none !important;}
</style>
<script>
    // Aggressive sidebar hide
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
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# Read query params (set by JS geolocation)
params = st.query_params
if params.get("lat") and params.get("lon") and not st.session_state.gps_loaded:
    try:
        lr = params.get("lat")
        lo = params.get("lon")
        if isinstance(lr, (list, tuple)) and len(lr) > 0:
            lr = lr[0]
        if isinstance(lo, (list, tuple)) and len(lo) > 0:
            lo = lo[0]
        lat_parsed = float(str(lr))
        lon_parsed = float(str(lo))
        if abs(lat_parsed) > 0.001 and abs(lon_parsed) > 0.001:
            st.session_state.gps_lat = lat_parsed
            st.session_state.gps_lon = lon_parsed
            st.session_state.gps_loaded = True
            src = params.get("src", "gps")
            if isinstance(src, (list, tuple)):
                src = src[0]
            st.session_state.gps_source = str(src)
    except Exception:
        pass

lat_val = float(st.session_state.gps_lat)
lon_val = float(st.session_state.gps_lon)

station = get_default_station()
station_name = station["name"] if station is not None else "Police"

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
    .ch {text-align:center; padding:1.5rem 0 1rem; border-bottom:2px solid #1a0a0a; margin-bottom:1.5rem}
    .ch h1 {font-size:2.2rem; font-weight:900; color:#f33; text-transform:uppercase; letter-spacing:6px; margin:0; text-shadow:0 0 20px rgba(255,0,0,.4)}
    .ch p {color:#555; font-size:.85rem; letter-spacing:3px; text-transform:uppercase; margin:.3rem 0 0}
    .sl {color:#f44; font-size:.7rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:.6rem; font-weight:bold}
    .slb {color:#4B8BFF; font-size:.7rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:.6rem; font-weight:bold}
    .gb {background:linear-gradient(145deg,#0d0d1a,#111122); border:1px solid #1a1a3a; border-radius:10px; padding:1rem; text-align:center}
    .gc {font-family:'Courier New',monospace; color:#0f8; font-size:1.1rem; font-weight:bold}
    .gl {color:#555; font-size:.7rem; text-transform:uppercase; letter-spacing:2px}
    .so {background:linear-gradient(135deg,#0a2a0a,#1a3a1a); border:1px solid #0f4; border-radius:10px; padding:1.2rem; margin:1rem 0}
    .so h3 {color:#0f8; margin-top:0; font-size:1.1rem}
    .dr {display:flex; justify-content:space-between; padding:.4rem 0; border-bottom:1px solid #1a3a1a; font-size:.85rem}
    .dl {color:#888} .dv {color:#fff; font-weight:bold}
    .fc {text-align:center; color:#444; font-size:.75rem; margin-top:2rem; padding:1rem 0; border-top:1px solid #1a1a1a}
    .fc a {color:#4B8BFF; text-decoration:none}
    .gps-ok {color:#0f8; font-size:.9rem; font-weight:bold}
    .gps-warn {color:#f80; font-size:.85rem}
    .manual-box {background:linear-gradient(145deg,#1a1a2e,#0d0d1a); border:1px solid #333; border-radius:8px; padding:1rem; margin-top:.5rem}
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
# GPS LOCALISATION - Robust multi-method
# ========================================
st.markdown('<div class="slb">2. Localisation GPS</div>', unsafe_allow_html=True)

# ---- METHOD 1: Server-side IP geolocation (most reliable on Streamlit Cloud) ----
if st.button("🌐 LOCALISER PAR IP (SERVEUR)", type="secondary", use_container_width=True):
    with st.spinner("Recherche de position via IP..."):
        try:
            # Try multiple IP geolocation services
            location_found = False
            # Service 1: ipapi.co
            try:
                resp = requests.get("https://ipapi.co/json/", timeout=10, headers={"User-Agent": "MutuAlert/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("latitude") and data.get("longitude"):
                        st.session_state.gps_lat = float(data["latitude"])
                        st.session_state.gps_lon = float(data["longitude"])
                        st.session_state.gps_loaded = True
                        st.session_state.gps_source = f"ip-{data.get('city', 'unknown')}"
                        location_found = True
                        st.success(f"✅ Position trouvee: {data.get('city', '')}, {data.get('country_name', '')}")
                        time.sleep(1)
                        st.rerun()
            except Exception:
                pass

            # Service 2: ipinfo.io (fallback)
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
                            st.session_state.gps_source = f"ip2-{data.get('city', 'unknown')}"
                            location_found = True
                            st.success(f"✅ Position trouvee: {data.get('city', '')}")
                            time.sleep(1)
                            st.rerun()
                except Exception:
                    pass

            if not location_found:
                st.error("❌ Localisation IP impossible. Saisissez manuellement.")
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")

# ---- METHOD 2: JavaScript GPS (works on mobile/direct access) ----
st.markdown("<div style='margin:.3rem 0'></div>", unsafe_allow_html=True)
gps_html = """
<div class="gb" id="gps-box">
    <button onclick="getGPS()" style="background:linear-gradient(135deg,#1a237e,#283593);color:white;border:none;padding:.8rem 1.5rem;border-radius:8px;font-size:.95rem;font-weight:bold;cursor:pointer;width:100%;letter-spacing:1px;text-transform:uppercase">
        📍 LOCALISER MA POSITION (GPS)
    </button>
    <div id="gps-out" style="margin-top:.8rem;font-family:monospace;font-size:.85rem;min-height:50px">
        <span style="color:#666">Cliquez pour obtenir vos coordonnees GPS (fonctionne sur mobile)</span>
    </div>
</div>
<script>
function getGPS(){
    var out=document.getElementById('gps-out');
    out.innerHTML='<span style="color:#4B8BFF">▶ Acquisition GPS en cours...</span>';
    if(!navigator.geolocation){
        out.innerHTML='<span style="color:#f44">✗ Geolocalisation non supportee.<br>Utilisez le bouton IP SERVEUR ci-dessus.</span>';
        return;
    }
    navigator.geolocation.getCurrentPosition(
        function(pos){
            var lat=pos.coords.latitude.toFixed(6);
            var lon=pos.coords.longitude.toFixed(6);
            var acc=Math.round(pos.coords.accuracy);
            out.innerHTML='<span style="color:#0f8">✓ GPS OK</span><br><span style="color:#ccc">LAT: '+lat+' | LON: '+lon+' | +/-'+acc+'m</span><br><span style="color:#4B8BFF">Chargement...</span>';
            var url=new URL(window.location.href);
            url.searchParams.set('lat',lat);
            url.searchParams.set('lon',lon);
            url.searchParams.set('src','gps');
            window.location.href=url.toString();
        },
        function(err){
            var msg='Erreur GPS: ';
            if(err.code==1)msg+='Permission refusee. Utilisez le bouton IP SERVEUR.';
            else if(err.code==2)msg+='Signal indisponible.';
            else msg+='Delai depasse.';
            out.innerHTML='<span style="color:#f80">⚠ '+msg+'</span>';
        },
        {enableHighAccuracy:true,timeout:15000,maximumAge:0}
    );
}
</script>
"""
st.components.v1.html(gps_html, height=150)

# ========================================
# GPS STATUS & RESET
# ========================================
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
            '<div class="gps-warn">⚠ Aucune position. Cliquez sur LOCALISER PAR IP (SERVEUR) ou saisissez manuellement.</div>',
            unsafe_allow_html=True,
        )

with c2:
    if st.button("🔄 Reset / Rafraichir", use_container_width=True):
        st.query_params.clear()
        st.session_state.gps_lat = 0.0
        st.session_state.gps_lon = 0.0
        st.session_state.gps_loaded = False
        st.session_state.gps_source = ""
        st.rerun()

# ========================================
# MANUAL ENTRY
# ========================================
st.markdown(
    "<div class='manual-box'><p style='color:#888;font-size:.8rem;margin:0 0 .5rem 0'>"
    "📝 Si les methodes automatiques echouent, saisissez manuellement :</p></div>",
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
        st.error("❌ Coordonnees invalides ou vides. Localisez-vous ou saisissez les coordonnees.")
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
    st.warning("⚠️ Localisez-vous (bouton IP SERVEUR en haut) ou saisissez les coordonnees GPS manuellement.")

# ========================================
# SUCCESS
# ========================================
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
        for k in ["alert_sent", "alert_id", "alert_lat", "alert_lon", "gps_lat", "gps_lon", "gps_loaded", "gps_source"]:
            if k in ("gps_lat", "gps_lon", "alert_lat", "alert_lon"):
                st.session_state[k] = 0.0
            elif k in ("alert_sent", "gps_loaded"):
                st.session_state[k] = False
            elif k == "gps_source":
                st.session_state[k] = ""
            else:
                st.session_state[k] = None
        st.query_params.clear()
        st.rerun()

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
if st.button("← RETOUR ACCUEIL", key="back_home"):
    st.switch_page("streamlit_app.py")

st.markdown(
    f"""<div class="fc"><b>MutuAlert</b> &copy; 2026 | Powered by """
    f"""<a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves</div>""",
    unsafe_allow_html=True,
)
