import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="MutuAlert - Alerte Urgence", page_icon="🚨", layout="centered")

st.markdown("""
<style>
    [data-testid="stSidebarNav"]{display:none!important}
    section[data-testid="stSidebar"]{display:none!important}
    button[kind="header"]{display:none!important}
    .stApp>header{display:none!important}
</style>
""", unsafe_allow_html=True)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.modules.database import init_db, create_alert, get_default_station
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

# === GPS - LECTURE DES COORDONNEES ===
query = st.query_params
has_gps_from_url = False
if "lat" in query and "lon" in query:
    try:
        lat_raw = query.get("lat")
        lon_raw = query.get("lon")
        if isinstance(lat_raw, list): lat_raw = lat_raw[0]
        if isinstance(lon_raw, list): lon_raw = lon_raw[0]
        parsed_lat = float(str(lat_raw))
        parsed_lon = float(str(lon_raw))
        if parsed_lat != 0.0 and parsed_lon != 0.0:
            st.session_state.gps_lat = parsed_lat
            st.session_state.gps_lon = parsed_lon
            st.session_state.gps_loaded = True
            has_gps_from_url = True
    except: pass

for key in ["gps_lat","gps_lon","gps_loaded","alert_sent","alert_id"]:
    if key not in st.session_state:
        st.session_state[key] = 0.0 if key in ("gps_lat","gps_lon") else (False if key=="alert_sent" else (None if key=="alert_id" else False))

lat_input = st.session_state.gps_lat
lon_input = st.session_state.gps_lon

station = get_default_station()
station_name = station['name'] if station is not None else "Police"
station_lat = station['latitude'] if station is not None else 5.36
station_lon = station['longitude'] if station is not None else -4.0083

st.markdown("""
<style>
    @keyframes pulse-ring { 0%{transform:scale(.85);opacity:1} 70%{transform:scale(1.5);opacity:0} 100%{transform:scale(1.5);opacity:0} }
    @keyframes heartbeat { 0%,100%{transform:scale(1)} 14%{transform:scale(1.05)} 28%{transform:scale(1)} 42%{transform:scale(1.05)} 70%{transform:scale(1)} }
    .ch{text-align:center;padding:1.5rem 0 1rem;border-bottom:2px solid #1a0a0a;margin-bottom:1.5rem}
    .ch h1{font-size:2.2rem;font-weight:900;color:#f33;text-transform:uppercase;letter-spacing:6px;margin:0;text-shadow:0 0 20px rgba(255,0,0,.4)}
    .ch p{color:#555;font-size:.85rem;letter-spacing:3px;text-transform:uppercase;margin:.3rem 0 0}
    .sl{color:#f44;font-size:.7rem;text-transform:uppercase;letter-spacing:3px;margin-bottom:.6rem;font-weight:bold}
    .slb{color:#4B8BFF;font-size:.7rem;text-transform:uppercase;letter-spacing:3px;margin-bottom:.6rem;font-weight:bold}
    .gb{background:linear-gradient(145deg,#0d0d1a,#111122);border:1px solid #1a1a3a;border-radius:10px;padding:1rem;text-align:center}
    .gc{font-family:'Courier New',monospace;color:#0f8;font-size:1.1rem;font-weight:bold}
    .gl{color:#555;font-size:.7rem;text-transform:uppercase;letter-spacing:2px}
    .so{background:linear-gradient(135deg,#0a2a0a,#1a3a1a);border:1px solid #0f4;border-radius:10px;padding:1.2rem;margin:1rem 0}
    .so h3{color:#0f4;margin-top:0;font-size:1.1rem}
    .dr{display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid #1a3a1a;font-size:.85rem}
    .dl{color:#888}.dv{color:#fff;font-weight:bold}
    .fc{text-align:center;color:#444;font-size:.75rem;margin-top:2rem;padding:1rem 0;border-top:1px solid #1a1a1a}
    .fc a{color:#4B8BFF;text-decoration:none}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="ch"><h1>🚨 MUTU ALERT</h1><p>Alerte d\'urgence - Envoyez votre position</p></div>', unsafe_allow_html=True)

# === TYPE ===
st.markdown('<div class="sl">1. Type d\'alerte</div>', unsafe_allow_html=True)
alert_type = st.segmented_control("", ["danger","medical","fire","suspicious","other"],
    format_func=lambda x:{"danger":"🆘 DANGER","medical":"🏥 MEDICAL","fire":"🔥 INCENDIE","suspicious":"👁 SUSPECT","other":"⚠️ AUTRE"}.get(x,x), default="danger")

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# === GPS ===
st.markdown('<div class="slb">2. Localisation GPS</div>', unsafe_allow_html=True)

geo_html = """
<div class="gb">
    <button onclick="getGPS()" style="background:linear-gradient(135deg,#1a237e,#283593);color:white;border:none;padding:.8rem 1.5rem;border-radius:8px;font-size:.95rem;font-weight:bold;cursor:pointer;width:100%;letter-spacing:1px;text-transform:uppercase">📍 Localiser ma position GPS</button>
    <div id="geo-status" style="margin-top:.6rem;font-family:monospace;font-size:.8rem"><span style="color:#666">Cliquez pour obtenir vos coordonnees GPS</span></div>
</div>
<script>
function getGPS(){
    var s=document.getElementById('geo-status');
    if(!navigator.geolocation){s.innerHTML='<span style="color:#f44">Geolocalisation non supportee</span>';return;}
    s.innerHTML='<span style="color:#4B8BFF"> Acquisition satellites... Patientez</span>';
    navigator.geolocation.getCurrentPosition(
        function(p){
            var lat=p.coords.latitude.toFixed(6),lon=p.coords.longitude.toFixed(6),acc=Math.round(p.coords.accuracy);
            s.innerHTML='<span style="color:#0f8">✓ POSITION ACQUISE</span><br><span style="color:#aaa">LAT: '+lat+' | LON: '+lon+' | ACC: ±'+acc+'m</span><br><span style="color:#4B8BFF;font-size:.75rem">Chargement...</span>';
            var u=new URL(window.location.href);u.searchParams.set('lat',lat);u.searchParams.set('lon',lon);window.location.href=u.toString();
        },
        function(e){var m='Erreur GPS. ';if(e.code==1)m+='Permission refusee.';else if(e.code==2)m+='Signal indisponible.';else m+='Delai depasse.';s.innerHTML='<span style="color:#f44">'+m+'</span>';},
        {enableHighAccuracy:true,timeout:20000,maximumAge:0}
    );
}
</script>"""
st.components.v1.html(geo_html, height=140)

if st.session_state.gps_loaded and lat_input!=0.0 and lon_input!=0.0: st.success(f"✓ GPS charge : {lat_input:.6f}, {lon_input:.6f}")
else: st.info("📍 Cliquez sur 'Localiser ma position' ou saisissez manuellement")

st.markdown("<p style='color:#444;font-size:.7rem;text-align:center;margin:.5rem 0'>Saisie manuelle :</p>", unsafe_allow_html=True)
c1,c2=st.columns(2)
with c1: manual_lat=st.number_input("LATITUDE",value=lat_input,format="%.6f",step=0.000001,key="man_lat")
with c2: manual_lon=st.number_input("LONGITUDE",value=lon_input,format="%.6f",step=0.000001,key="man_lon")
if manual_lat!=lat_input: st.session_state.gps_lat=manual_lat; lat_input=manual_lat
if manual_lon!=lon_input: st.session_state.gps_lon=manual_lon; lon_input=manual_lon

c1,c2,c3=st.columns(3)
with c1: st.markdown(f'<div class="gb"><div class="gl">LATITUDE</div><div class="gc">{lat_input:.6f}</div></div>',unsafe_allow_html=True)
with c2: st.markdown(f'<div class="gb"><div class="gl">LONGITUDE</div><div class="gc">{lon_input:.6f}</div></div>',unsafe_allow_html=True)
with c3: is_valid=validate_coordinates(lat_input,lon_input); st.markdown(f'<div class="gb"><div class="gl">STATUT</div><div class="gc" style="color:{",".join(["#0f8" if is_valid else "#f44",""])}">{"VALIDE" if is_valid else "INVALIDE"}</div></div>',unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>",unsafe_allow_html=True)

# === DETAILS ===
st.markdown('<div class="slb">3. Details (optionnels)</div>',unsafe_allow_html=True)
desc=st.text_area("",placeholder="Decrivez la situation...",height=70,key="desc_field",label_visibility="collapsed")
phone=st.text_input("Tel contact (optionnel)",placeholder="+225 XX XX XX XX",key="phone_field")

# === EMERGENCY BUTTON ===
st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
st.markdown('<div class="sl">4. Envoyer l\'alerte</div>',unsafe_allow_html=True)

has_valid=validate_coordinates(lat_input,lon_input)

st.markdown("""
<div style="position:relative;width:260px;height:100px;margin:0 auto;display:flex;align-items:center;justify-content:center">
    <div style="position:absolute;width:200px;height:200px;border-radius:50%;border:3px solid rgba(255,0,0,.2);animation:pulse-ring 2.5s infinite"></div>
    <div style="position:absolute;width:200px;height:200px;border-radius:50%;border:2px solid rgba(255,0,0,.15);animation:pulse-ring 3s infinite"></div>
</div>""",unsafe_allow_html=True)

if st.button("ALERTE\nURGENCE",key="big_red_btn",type="primary",disabled=not has_valid):
    if not has_valid: st.error("❌ Coordonnees invalides")
    else:
        with st.spinner("TRANSMISSION..."):
            try:
                aid=create_alert(alert_type=alert_type,latitude=lat_input,longitude=lon_input,accuracy=50.0,description=desc if desc else None,phone=phone if phone else None,device_id='web-'+str(hash(str(lat_input))%100000))
                st.session_state.alert_sent=True; st.session_state.alert_id=aid
                st.session_state.alert_lat=lat_input; st.session_state.alert_lon=lon_input
                time.sleep(1.5)
            except Exception as e: st.error(f"ERREUR: {str(e)}")

st.markdown("""
<style>
    [data-testid="stButton"]>button[kind="primary"]{width:200px!important;height:200px!important;border-radius:50%!important;background:radial-gradient(circle at 35% 35%,#f55,#c00,#800)!important;color:#fff!important;font-size:1.5rem!important;font-weight:900!important;border:3px solid #f88!important;box-shadow:0 0 30px rgba(255,0,0,.5),inset 0 0 40px rgba(0,0,0,.3)!important;animation:heartbeat 2s infinite!important;line-height:1.2!important;white-space:pre-line!important;display:block;margin:0 auto}
    [data-testid="stButton"]>button[kind="primary"]:hover{transform:scale(1.08)!important;background:radial-gradient(circle at 35% 35%,#f77,#d00,#a00)!important}
    [data-testid="stButton"]>button[kind="primary"]:disabled{background:#222!important;border-color:#444!important;color:#555!important;animation:none!important;box-shadow:none!important}
</style>""",unsafe_allow_html=True)

if not has_valid: st.warning("⚠️ Localisez-vous ou saisissez les coordonnees GPS avant d'envoyer.")

# === SUCCESS ===
if st.session_state.alert_sent:
    st.balloons()
    st.markdown(f"""
    <div class="so">
        <h3>✅ ALERTE #{st.session_state.alert_id} CONFIRMEE</h3>
        <div class="dr"><span class="dl">TYPE</span><span class="dv">{get_alert_label(alert_type)}</span></div>
        <div class="dr"><span class="dl">POSITION</span><span class="dv">{get_location_display(lat_input,lon_input)}</span></div>
        <div class="dr"><span class="dl">HEURE</span><span class="dv">{datetime.now().strftime('%H:%M:%S')}</span></div>
        <div class="dr"><span class="dl">POSTE POLICE</span><span class="dv" style="color:#4B8BFF">{station_name}</span></div>
        <div class="dr"><span class="dl">STATUT</span><span class="dv" style="color:#0f8">● ACTIVE - POLICE NOTIFIEE</span></div>
    </div>""",unsafe_allow_html=True)
    st.info("Restez calme. La police a recu votre position exacte et est en route.")
    if st.button("🗺 VOIR LE TRAJET DE LA POLICE",type="secondary",use_container_width=True): st.switch_page("pages/trajet.py")
    if st.button("NOUVELLE ALERTE",type="secondary"):
        for k in ['alert_sent','alert_id','alert_lat','alert_lon','gps_lat','gps_lon','gps_loaded']:
            if k in st.session_state:
                st.session_state[k] = 0.0 if k in ('gps_lat','gps_lon','alert_lat','alert_lon') else (False if k in ('alert_sent','gps_loaded') else None)
        st.query_params.clear(); st.rerun()

st.markdown("<div style='height:30px'></div>",unsafe_allow_html=True)
if st.button("← RETOUR ACCUEIL",key="back_home"): st.switch_page("streamlit_app.py")

st.markdown(f"""<div class="fc"><b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves</div>""",unsafe_allow_html=True)
