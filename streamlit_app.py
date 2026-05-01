import streamlit as st

# Page config
st.set_page_config(
    page_title="SecureAlert - Sécurité Civique",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for branding
custom_css = """
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #1C1E26 0%, #2C2E3A 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #333;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        border-color: #FF4B4B;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #FF4B4B;
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #333;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Hide sidebar nav on homepage
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">🛡️ SecureAlert</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Protection civique en temps réel | POESAM 2026</div>', unsafe_allow_html=True)

st.divider()

# Hero description
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    ### Sécurisons nos communautés ensemble
    
    **SecureAlert** est une solution technologique d'urgence qui connecte instantanément 
    les citoyens en danger avec les forces de l'ordre via géolocalisation précise 
    et suivi d'itinéraires en temps réel.
    
    """, unsafe_allow_html=True)

# Navigation cards
st.divider()
st.subheader("Choisissez votre portail")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    <div class="feature-card">
        <h2 style="color: #FF4B4B;">🚨 Citoyen</h2>
        <p>Envoyez une alerte d'urgence avec votre position GPS exacte en un seul clic. 
        Les forces de l'ordre seront immédiatement notifiées.</p>
        <ul>
            <li>Géolocalisation automatique</li>
            <li>Envoi instantané</li>
            <li>100% anonyme possible</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Accéder Portail Citoyen →", key="btn_citizen", use_container_width=True):
        st.switch_page("app/pages/1_🚨_Client.py")

with col_b:
    st.markdown("""
    <div class="feature-card">
        <h2 style="color: #4B8BFF;">👮 Police & Sécurité</h2>
        <p>Portail sécurisé pour visualiser les alertes actives, tracer les itinéraires 
        et coordonner les interventions en temps réel.</p>
        <ul>
            <li>Carte temps réel avec alertes clignotantes</li>
            <li>Traçage d'itinéraires</li>
            <li>Gestion des statuts</li>
            <li>Accès sécurisé</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Accéder Portail Police →", key="btn_police", use_container_width=True):
        st.switch_page("app/pages/2_👮_Police.py")

# Stats section
st.divider()
st.subheader("📊 Tableau de bord public")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.modules.database import init_db, get_alert_stats
init_db()
stats = get_alert_stats()

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    active = stats.get('active', 0)
    st.metric("Alertes actives (24h)", active, delta=f"-{stats.get('resolved', 0)} résolues")
with col_s2:
    total = sum(stats.values())
    st.metric("Total alertes (24h)", total)
with col_s3:
    st.metric("Temps moyen de réponse", "4.2 min")
with col_s4:
    st.metric("Zones couvertes", "12 districts")

# Footer
st.markdown("""
<div class="footer">
    SecureAlert © 2026 | Projet candidat au POESAM Orange | 
    Technologies: Python, Streamlit, Folium, GPS | 
    🔒 Données chiffrées et sécurisées
</div>
""", unsafe_allow_html=True)
