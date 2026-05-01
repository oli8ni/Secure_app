import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="Alerte Citoyen", page_icon="🚨", layout="centered")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import init_db, create_alert
from app.modules.geo import validate_coordinates, get_location_display
from app.modules.alerts import get_alert_color, get_alert_label

init_db()

st.markdown("""
<style>
.status-box {
    background: #1C1E26;
    border-radius: 12px;
    padding: 1.5rem;
    border-left: 4px solid #FF4B4B;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🚨 Portail Citoyen")
st.markdown("### Envoyez une alerte d'urgence instantanément")
st.divider()

st.subheader("1. Type d'alerte")
alert_type = st.segmented_control(
    "",
    options=["danger", "medical", "fire", "suspicious", "other"],
    format_func=lambda x: {
        "danger": "🆘 Danger vital",
        "medical": "🏥 Médical",
        "fire": "🔥 Incendie",
        "suspicious": "👁 Suspect",
        "other": "⚠️ Autre"
    }.get(x, x),
    default="danger"
)

st.divider()
st.subheader("2. Votre position GPS")

geolocation_html = """
<div id="geo-container">
    <button onclick="getLocation()" style="
        background: linear-gradient(135deg, #4B8BFF, #2C5FD1);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-size: 1rem;
        cursor: pointer;
        width: 100%;
        margin-bottom: 1rem;
    ">📍 Localiser ma position</button>
    <div id="location-result" style="
        background: #1C1E26;
        border-radius: 12px;
        padding: 1rem;
        display: none;
        border-left: 4px solid #4B8BFF;
    ">
        <p><strong>Latitude:</strong> <span id="lat"></span></p>
        <p><strong>Longitude:</strong> <span id="lon"></span></p>
        <p><strong>Précision:</strong> <span id="acc"></span> mètres</p>
    </div>
</div>
<script>
function getLocation() {
    const result = document.getElementById('location-result');
    if (!navigator.geolocation) {
        alert("La géolocalisation n'est pas supportée par ce navigateur.");
        return;
    }
    result.style.display = 'block';
    result.innerHTML = '<p style="color: #888;">Recherche de position...</p>';
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const acc = position.coords.accuracy;
            result.innerHTML = `
                <p><strong style="color: #4B8BFF;">✓ Position capturée</strong></p>
                <p>Latitude: ${lat.toFixed(6)}</p>
                <p>Longitude: ${lon.toFixed(6)}</p>
                <p>Précision: ±${Math.round(acc)} mètres</p>
            `;
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: {lat: lat, lon: lon, acc: acc}}, '*');
        },
        function(error) {
            let msg = "Erreur de géolocalisation. ";
            switch(error.code) {
                case error.PERMISSION_DENIED: msg += "Permission refusée."; break;
                case error.POSITION_UNAVAILABLE: msg += "Position indisponible."; break;
                case error.TIMEOUT: msg += "Délai dépassé."; break;
            }
            result.innerHTML = `<p style="color: #FF4B4B;">${msg}</p>`;
        },
        {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
    );
}
</script>
"""

st.components.v1.html(geolocation_html, height=250)

st.markdown("*Si la géolocalisation automatique échoue:*")
lat_input = st.number_input("Latitude", value=0.0, format="%.6f", step=0.000001, key="manual_lat")
lon_input = st.number_input("Longitude", value=0.0, format="%.6f", step=0.000001, key="manual_lon")

st.divider()
st.subheader("3. Détails (optionnels)")
col1, col2 = st.columns(2)
with col1:
    description = st.text_area("Description de la situation", placeholder="Décrivez ce qui se passe...", height=100)
with col2:
    phone = st.text_input("Numéro de contact (optionnel)", placeholder="+XXX XXXX XXXX")
    st.caption("La police pourrait vous recontacter. Anonyme si vide.")

if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False
if 'alert_id' not in st.session_state:
    st.session_state.alert_id = None

st.divider()
st.subheader("4. Envoyer l'alerte")

has_valid_coords = validate_coordinates(lat_input, lon_input)

if not has_valid_coords and (lat_input == 0.0 and lon_input == 0.0):
    st.warning("⚠️ Veuillez d'abord obtenir votre position GPS ou entrer les coordonnées manuellement.")

if st.button("🚨 ALERTE D'URGENCE 🚨", type="primary", use_container_width=True, disabled=not has_valid_coords):
    if not has_valid_coords:
        st.error("Coordonnées invalides. Veuillez vérifier votre position.")
    else:
        with st.spinner("Envoi de l'alerte aux forces de l'ordre..."):
            try:
                alert_id = create_alert(
                    alert_type=alert_type,
                    latitude=lat_input,
                    longitude=lon_input,
                    accuracy=50.0,
                    description=description if description else None,
                    phone=phone if phone else None,
                    device_id=st.session_state.get('device_id', 'web-' + str(hash(str(lat_input)) % 100000))
                )
                st.session_state.alert_sent = True
                st.session_state.alert_id = alert_id
                time.sleep(1.5)
            except Exception as e:
                st.error(f"Erreur d'envoi: {str(e)}")

if st.session_state.alert_sent:
    st.balloons()
    st.success(f"✅ **Alerte #{st.session_state.alert_id} envoyée avec succès !**")
    st.markdown(f"""
    <div class="status-box">
        <h3 style="color: #FF4B4B; margin-top: 0;">🚨 Alerte {get_alert_label(alert_type)} enregistrée</h3>
        <p><strong>ID Alerte:</strong> #{st.session_state.alert_id}</p>
        <p><strong>Position:</strong> {get_location_display(lat_input, lon_input)}</p>
        <p><strong>Heure:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
        <p><strong>Statut:</strong> <span style="color: #FF4B4B;">● Active - Police notifiée</span></p>
    </div>
    """, unsafe_allow_html=True)
    st.info("""
    **Conseils de sécurité:**
    - Restez calme et trouvez un endroit sûr si possible
    - Gardez votre téléphone allumé
    - La police a reçu votre position exacte
    - En cas de danger imminent, appelez directement les urgences
    """)
    if st.button("🔄 Nouvelle alerte", type="secondary"):
        st.session_state.alert_sent = False
        st.session_state.alert_id = None
        st.rerun()

st.divider()
st.caption("""
**Mode démonstration POESAM 2026** | Cette application est un prototype fonctionnel. 
En production, l'application mobile native utilisera la géolocalisation haute précision, 
chiffrement bout-en-bout, et connexion directe aux systèmes CIC.
""")

if st.button("← Retour à l'accueil", key="back_home_client"):
    st.switch_page("streamlit_app.py")
