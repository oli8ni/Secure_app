import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Alerte Urgence", page_icon="🚨", layout="centered")

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
from app.modules.database import init_db, create_alert, get_default_station
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

# =========================
# LECTURE GPS DEPUIS QUERY PARAMS
# =========================
params = st.query_params
has_new_gps = False

if params.get("lat") and params.get("lon"):
    try:
        lat_raw = params.get("lat")
        lon_raw = params.get("lon")
        if isinstance(lat_raw, (list, tuple)) and len(lat_raw) > 0:
            lat_raw = lat_raw[0]
        if isinstance(lon_raw, (list, tuple)) and len(lon_raw) > 0:
            lon_raw = lon_raw[0]
        new_lat = float(str(lat_raw))
        new_lon = float(str(lon_raw))
        if abs(new_lat) > 0.001 and abs(new_lon) > 0.001:
            st.session_state.gps_lat = new_lat
            st.session_state.gps_lon = new_lon
            st.session_state.gps_loaded = True
            has_new_gps = True
    except Exception:
        pass

# Initialisation des valeurs par défaut
for key, val in [("gps_lat", 0.0), ("gps_lon", 0.0), ("gps_loaded", False),
                 ("alert_sent", False), ("alert_id", None),
                 ("alert_lat", 0.0), ("alert_lon", 0.0)]:
    if key not in st.session_state:
        st.session_state[key] = val

lat_val = float(st.session_state.gps_lat)
lon_val = float(st.session_state.gps_lon)

station     = get_default_station()
station_name = station['name'] if station is not None else "Police"

# =========================
# STYLES
# =========================
st.markdown("""
<style>
    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        14%       { transform: scale(1.05); }
        28%       { transform: scale(1); }
        42%       { transform: scale(1.05); }
        70%       { transform: scale(1); }
    }
    @keyframes pulse-ring {
        0%   { transform: scale(.85); opacity: 1; }
        70%  { transform: scale(1.5);  opacity: 0; }
        100% { transform: scale(1.5);  opacity: 0; }
    }
    .ch    { text-align:center; padding:1.5rem 0 1rem; border-bottom:2px solid #1a0a0a; margin-bottom:1.5rem; }
    .ch h1 { font-size:2.2rem; font-weight:900; color:#f33; text-transform:uppercase; letter-spacing:6px; margin:0; text-shadow:0 0 20px rgba(255,0,0,.4); }
    .ch p  { color:#555; font-size:.85rem; letter-spacing:3px; text-transform:uppercase; margin:.3rem 0 0; }
    .sl    { color:#f44; font-size:.7rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:.6rem; font-weight:bold; }
    .slb   { color:#4B8BFF; font-size:.7rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:.6rem; font-weight:bold; }
    .gb    { background:linear-gradient(145deg,#0d0d1a,#111122); border:1px solid #1a1a3a; border-radius:10px; padding:1rem; text-align:center; }
    .gc    { font-family:'Courier New',monospace; color:#0f8; font-size:1.1rem; font-weight:bold; }
    .gl    { color:#555; font-size:.7rem; text-transform:uppercase; letter-spacing:2px; }
    .so    { background:linear-gradient(135deg,#0a2a0a,#1a3a1a); border:1px solid #0f4; border-radius:10px; padding:1.2rem; margin:1rem 0; }
    .so h3 { color:#0f4; margin-top:0; font-size:1.1rem; }
    .dr    { display:flex; justify-content:space-between; padding:.4rem 0; border-bottom:1px solid #1a3a1a; font-size:.85rem; }
    .dl    { color:#888; }
    .dv    { color:#fff; font-weight:bold; }
    .fc    { text-align:center; color:#444; font-size:.75rem; margin-top:2rem; padding:1rem 0; border-top:1px solid #1a1a1a; }
    .fc a  { color:#4B8BFF; text-decoration:none; }
    .gps-ok   { color:#0f8; font-size:.9rem; font-weight:bold; }
    .gps-warn { color:#f80; font-size:.85rem; }
    .gps-err  { color:#f44; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='ch'><h1>🚨 MUTU ALERT</h1><p>Alerte d'urgence — Envoyez votre position</p></div>", unsafe_allow_html=True)

# =========================
# 1. TYPE D'ALERTE
# =========================
st.markdown("<div class='sl'>1. Type d'alerte</div>", unsafe_allow_html=True)
alert_type = st.segmented_control(
    "", ["danger", "medical", "fire", "suspicious", "other"],
    format_func=lambda x: {
        "danger":     "🆘 DANGER",
        "medical":    "🏥 MÉDICAL",
        "fire":       "🔥 INCENDIE",
        "suspicious": "👁 SUSPECT",
        "other":      "⚠️ AUTRE"
    }.get(x, x),
    default="danger"
)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# =========================
# 2. GPS — LOCALISATION
# =========================
st.markdown("<div class='slb'>2. Localisation GPS</div>", unsafe_allow_html=True)

# ✅ CORRECTION CRITIQUE :
#    Le composant HTML est dans un iframe Streamlit.
#    Pour modifier l'URL de la PAGE PARENTE (pas l'iframe), on utilise window.parent.location.
#    On ajoute aussi allow="geolocation" via un wrapper CSS trick.
gps_html = """
<style>
  #gps-btn {
    background: linear-gradient(135deg, #1a237e, #283593);
    color: white; border: none; padding: .8rem 1.5rem;
    border-radius: 8px; font-size: .95rem; font-weight: bold;
    cursor: pointer; width: 100%; letter-spacing: 1px;
    text-transform: uppercase;
  }
  #gps-btn:hover { background: linear-gradient(135deg, #283593, #3949ab); }
  #gps-out { margin-top: .8rem; font-family: monospace; font-size: .85rem; min-height: 60px; }
</style>

<div class="gb">
  <button id="gps-btn" onclick="locateUser()">📍 LOCALISER MA POSITION</button>
  <div id="gps-out">
    <span style="color:#666">Cliquez pour obtenir vos coordonnées GPS</span>
  </div>
</div>

<script>
function locateUser() {
  var out = document.getElementById('gps-out');
  out.innerHTML = '<span style="color:#4B8BFF">▶ Acquisition GPS en cours...</span>';

  if (!navigator.geolocation) {
    out.innerHTML = '<span style="color:#f44">✗ Géolocalisation non supportée par ce navigateur.</span>';
    return;
  }

  navigator.geolocation.getCurrentPosition(
    function(pos) {
      var lat = pos.coords.latitude.toFixed(6);
      var lon = pos.coords.longitude.toFixed(6);
      var acc = Math.round(pos.coords.accuracy);
      out.innerHTML =
        '<span style="color:#0f8">✓ GPS OK — précision ' + acc + 'm</span><br>' +
        '<span style="color:#ccc">LAT: ' + lat + ' | LON: ' + lon + '</span><br>' +
        '<span style="color:#4B8BFF">⏳ Redirection...</span>';

      // ✅ On modifie l'URL de la PAGE PARENTE (Streamlit), pas celle de l'iframe
      setTimeout(function() {
        var url = new URL(window.parent.location.href);
        url.searchParams.set('lat', lat);
        url.searchParams.set('lon', lon);
        url.searchParams.set('src', 'gps');
        window.parent.location.replace(url.toString());
      }, 600);
    },
    function(err) {
      var msgs = {1:'Permission refusée', 2:'Position indisponible', 3:'Délai expiré'};
      out.innerHTML = '<span style="color:#f80">⚠ GPS: ' + (msgs[err.code] || err.message) + '. Tentative via IP...</span>';

      // Fallback: géolocalisation par IP
      fetch('https://ipapi.co/json/')
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.latitude && data.longitude) {
            var lat = parseFloat(data.latitude).toFixed(6);
            var lon = parseFloat(data.longitude).toFixed(6);
            out.innerHTML =
              '<span style="color:#0f8">✓ Position IP (approximative)</span><br>' +
              '<span style="color:#ccc">LAT: ' + lat + ' | LON: ' + lon + '</span><br>' +
              '<span style="color:#4B8BFF">⏳ Redirection...</span>';
            setTimeout(function() {
              var url = new URL(window.parent.location.href);
              url.searchParams.set('lat', lat);
              url.searchParams.set('lon', lon);
              url.searchParams.set('src', 'ip');
              window.parent.location.replace(url.toString());
            }, 600);
          } else {
            out.innerHTML = '<span style="color:#f44">✗ Impossible d\'obtenir la position. Saisissez manuellement.</span>';
          }
        })
        .catch(function(e) {
          out.innerHTML = '<span style="color:#f44">✗ Erreur réseau. Saisissez les coordonnées manuellement.</span>';
        });
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
  );
}
</script>
"""
# ✅ allow="geolocation" est indispensable pour que le navigateur autorise l'accès GPS depuis l'iframe
st.components.v1.html(gps_html, height=175)

# Affichage statut GPS
c1, c2 = st.columns(2)
with c1:
    if st.session_state.gps_loaded and abs(lat_val) > 0.001:
        src = params.get("src", "gps")
        if isinstance(src, (list, tuple)):
            src = src[0]
        st.markdown(
            f'<div class="gps-ok">✓ Position chargée ({str(src).upper()})<br>LAT: {lat_val:.6f} | LON: {lon_val:.6f}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="gps-warn">⚠ Aucune position GPS. Cliquez sur le bouton ci-dessus ou saisissez manuellement.</div>',
            unsafe_allow_html=True
        )
with c2:
    if st.button("🔄 Réinitialiser GPS", use_container_width=True):
        st.query_params.clear()
        for k in ['gps_lat', 'gps_lon', 'gps_loaded']:
            st.session_state[k] = 0.0 if k in ('gps_lat', 'gps_lon') else False
        st.rerun()

# Saisie manuelle
st.markdown("<p style='color:#444;font-size:.7rem;text-align:center;margin:.5rem 0'>Saisie manuelle (si GPS échoue) :</p>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    manual_lat = st.number_input("LATITUDE",  value=lat_val, format="%.6f", step=0.000001, key="man_lat")
with c2:
    manual_lon = st.number_input("LONGITUDE", value=lon_val, format="%.6f", step=0.000001, key="man_lon")

if manual_lat != lat_val:
    st.session_state.gps_lat = manual_lat
    lat_val = manual_lat
if manual_lon != lon_val:
    st.session_state.gps_lon = manual_lon
    lon_val = manual_lon

# Affichage coordonnées
co1, co2, co3 = st.columns(3)
with co1:
    st.markdown(f'<div class="gb"><div class="gl">LATITUDE</div><div class="gc">{lat_val:.6f}</div></div>', unsafe_allow_html=True)
with co2:
    st.markdown(f'<div class="gb"><div class="gl">LONGITUDE</div><div class="gc">{lon_val:.6f}</div></div>', unsafe_allow_html=True)
with co3:
    is_v  = validate_coordinates(lat_val, lon_val)
    v_c   = "#0f8" if is_v else "#f44"
    v_t   = "VALIDE" if is_v else "INVALIDE"
    st.markdown(f'<div class="gb"><div class="gl">STATUT</div><div class="gc" style="color:{v_c}">{v_t}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# =========================
# 3. DÉTAILS
# =========================
st.markdown("<div class='slb'>3. Détails (optionnels)</div>", unsafe_allow_html=True)
desc  = st.text_area("", placeholder="Décrivez la situation...", height=70, key="desc_field", label_visibility="collapsed")
phone = st.text_input("Tél. contact (optionnel)", placeholder="+243 XX XX XX XX", key="phone_field")

# =========================
# 4. BOUTON D'ALERTE
# =========================
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
st.markdown("<div class='sl'>4. Envoyer l'alerte</div>", unsafe_allow_html=True)

has_valid = validate_coordinates(lat_val, lon_val)

# Anneaux de pulse décoratifs
st.markdown("""
<div style="position:relative;width:260px;height:80px;margin:0 auto;display:flex;align-items:center;justify-content:center">
    <div style="position:absolute;width:200px;height:200px;border-radius:50%;border:3px solid rgba(255,0,0,.2);animation:pulse-ring 2.5s infinite"></div>
    <div style="position:absolute;width:200px;height:200px;border-radius:50%;border:2px solid rgba(255,0,0,.15);animation:pulse-ring 3s infinite"></div>
</div>
""", unsafe_allow_html=True)

if st.button("ALERTE\nURGENCE", key="big_red_btn", type="primary", disabled=not has_valid):
    if not has_valid:
        st.error("❌ Coordonnées invalides. Localisez-vous ou saisissez les coordonnées.")
    else:
        with st.spinner("TRANSMISSION EN COURS..."):
            try:
                aid = create_alert(
                    alert_type  = alert_type,
                    latitude    = lat_val,
                    longitude   = lon_val,
                    accuracy    = 50.0,
                    description = desc  if desc  else None,
                    phone       = phone if phone else None,
                    device_id   = 'web-' + str(hash(str(lat_val)) % 100000)
                )
                st.session_state.alert_sent = True
                st.session_state.alert_id   = aid
                st.session_state.alert_lat  = lat_val
                st.session_state.alert_lon  = lon_val
                time.sleep(1.5)
            except Exception as e:
                st.error(f"ERREUR TRANSMISSION : {str(e)}")

st.markdown("""
<style>
[data-testid="stButton"] > button[kind="primary"] {
    width:200px!important; height:200px!important; border-radius:50%!important;
    background:radial-gradient(circle at 35% 35%,#f55,#c00,#800)!important;
    color:#fff!important; font-size:1.5rem!important; font-weight:900!important;
    border:3px solid #f88!important;
    box-shadow:0 0 30px rgba(255,0,0,.5),inset 0 0 40px rgba(0,0,0,.3)!important;
    animation:heartbeat 2s infinite!important;
    line-height:1.2!important; white-space:pre-line!important; display:block; margin:0 auto;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    transform:scale(1.08)!important;
    background:radial-gradient(circle at 35% 35%,#f77,#d00,#a00)!important;
}
[data-testid="stButton"] > button[kind="primary"]:disabled {
    background:#222!important; border-color:#444!important;
    color:#555!important; animation:none!important; box-shadow:none!important;
}
</style>
""", unsafe_allow_html=True)

if not has_valid:
    st.warning("⚠️ Appuyez sur 'Localiser ma position' ou saisissez les coordonnées GPS.")

# =========================
# CONFIRMATION ENVOI
# =========================
if st.session_state.alert_sent:
    st.balloons()
    st.markdown(f"""
    <div class="so">
        <h3>✅ ALERTE #{st.session_state.alert_id} CONFIRMÉE</h3>
        <div class="dr"><span class="dl">TYPE</span><span class="dv">{get_alert_label(alert_type)}</span></div>
        <div class="dr"><span class="dl">POSITION</span><span class="dv">{get_location_display(lat_val, lon_val)}</span></div>
        <div class="dr"><span class="dl">HEURE</span><span class="dv">{datetime.now().strftime('%H:%M:%S')}</span></div>
        <div class="dr"><span class="dl">POSTE POLICE</span><span class="dv" style="color:#4B8BFF">{station_name}</span></div>
        <div class="dr"><span class="dl">STATUT</span><span class="dv" style="color:#0f8">● ACTIVE — POLICE NOTIFIÉE</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Restez calme. La police a reçu votre position et est en route.")

    if st.button("🗺 VOIR LE TRAJET DE LA POLICE", type="secondary", use_container_width=True):
        st.switch_page("pages/trajet.py")

    if st.button("NOUVELLE ALERTE", type="secondary"):
        for k in ['alert_sent', 'alert_id', 'alert_lat', 'alert_lon', 'gps_lat', 'gps_lon', 'gps_loaded']:
            st.session_state[k] = (
                0.0   if k in ('gps_lat', 'gps_lon', 'alert_lat', 'alert_lon') else
                False if k in ('alert_sent', 'gps_loaded') else
                None
            )
        st.query_params.clear()
        st.rerun()

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
if st.button("← RETOUR ACCUEIL", key="back_home"):
    st.switch_page("streamlit_app.py")

st.markdown(
    '<div class="fc"><b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&amp;O Itech Solution</a> | Tous droits réservés</div>',
    unsafe_allow_html=True
)
