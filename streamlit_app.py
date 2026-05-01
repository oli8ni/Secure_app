import streamlit as st

st.set_page_config(
    page_title="MutuAlert - Alertes Citoyennes",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === HIDE SIDEBAR NAVIGATION COMPLETELY ===
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    .stApp > header {display: none !important;}
    .reportview-container .main .block-container {padding-top: 0 !important;}
    @keyframes neonPulse {
        0%, 100% { box-shadow: 0 0 20px rgba(255,75,75,0.3), 0 0 40px rgba(255,0,0,0.1); }
        50% { box-shadow: 0 0 30px rgba(255,75,75,0.6), 0 0 60px rgba(255,0,0,0.3); }
    }
    @keyframes textGlow {
        0%, 100% { text-shadow: 0 0 10px rgba(255,75,75,0.4); }
        50% { text-shadow: 0 0 25px rgba(255,75,75,0.9), 0 0 50px rgba(255,0,0,0.3); }
    }
    .hero-section {
        position: relative;
        text-align: center;
        padding: 4rem 1rem 3rem 1rem;
        background: linear-gradient(180deg, rgba(10,10,20,0.9) 0%, rgba(5,5,10,0.95) 100%);
        border-bottom: 2px solid #1a1a3a;
        margin: -1rem -1rem 2rem -1rem;
    }
    .hero-logo {
        font-size: 3.5rem;
        font-weight: 900;
        letter-spacing: 6px;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF0000 50%, #CC0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textGlow 3s ease-in-out infinite;
        margin-bottom: 0.5rem;
    }
    .hero-tagline {
        color: #777;
        font-size: 1.1rem;
        letter-spacing: 4px;
        text-transform: uppercase;
    }
    .hero-desc {
        color: #aaa;
        max-width: 550px;
        margin: 1.5rem auto 0 auto;
        line-height: 1.7;
        font-size: 1rem;
    }
    .stat-card {
        background: linear-gradient(145deg, #141428 0%, #0d0d1a 100%);
        border: 1px solid #222244;
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s;
    }
    .stat-card:hover {
        border-color: #FF4B4B;
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(255,75,75,0.1);
    }
    .stat-num {
        font-size: 2.5rem;
        font-weight: 900;
        line-height: 1;
    }
    .stat-red { color: #FF4B4B; text-shadow: 0 0 15px rgba(255,75,75,0.3); }
    .stat-blue { color: #4B8BFF; text-shadow: 0 0 15px rgba(75,139,255,0.3); }
    .stat-green { color: #00CC88; text-shadow: 0 0 15px rgba(0,204,136,0.3); }
    .stat-lbl {
        font-size: 0.75rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.5rem;
    }
    .emergency-btn-container {
        text-align: center;
        padding: 3rem 0;
    }
    .emergency-label {
        color: #FF4B4B;
        font-size: 0.9rem;
        font-weight: bold;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    .feature-box {
        background: linear-gradient(145deg, #141428, #0d0d1a);
        border: 1px solid #222244;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .feature-title {
        color: #fff;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
    }
    .feature-desc {
        color: #777;
        font-size: 0.8rem;
    }
    .police-trigger {
        position: fixed;
        bottom: 15px;
        right: 15px;
        z-index: 9999;
        background: none;
        border: none;
        color: #333;
        font-size: 0.65rem;
        cursor: pointer;
        padding: 5px;
        transition: color 0.3s;
    }
    .police-trigger:hover { color: #555; }
    .footer-co {
        text-align: center;
        color: #444;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding: 1rem 0;
        border-top: 1px solid #1a1a1a;
    }
    .footer-co a {
        color: #4B8BFF;
        text-decoration: none;
    }
    .footer-co a:hover {
        color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# === HERO SECTION ===
st.markdown("""
<div class="hero-section">
    <div class="hero-logo">🛡️ MUTU ALERT</div>
    <div class="hero-tagline">Protection Civique en Temps Reel</div>
    <div class="hero-desc">
        <b>MutuAlert</b> connecte instantanement les citoyens en danger avec les forces de l'ordre. 
        Geolocalisation precise, suivi d'itineraires, reponse optimisee. Un clic. Une alerte. Une vie sauvee.
    </div>
</div>
""", unsafe_allow_html=True)

# === STATS ===
from app.modules.database import init_db, get_alert_stats
init_db()
stats = get_alert_stats()

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    active = stats.get('active', 0)
    st.markdown(f'<div class="stat-card"><div class="stat-num stat-red">{active}</div><div class="stat-lbl">Alertes Actives</div></div>', unsafe_allow_html=True)
with col_s2:
    total = sum(stats.values())
    st.markdown(f'<div class="stat-card"><div class="stat-num stat-red">{total}</div><div class="stat-lbl">Total 24h</div></div>', unsafe_allow_html=True)
with col_s3:
    st.markdown(f'<div class="stat-card"><div class="stat-num stat-blue">4.2</div><div class="stat-lbl">Min Response</div></div>', unsafe_allow_html=True)
with col_s4:
    st.markdown(f'<div class="stat-card"><div class="stat-num stat-green">12</div><div class="stat-lbl">Districts</div></div>', unsafe_allow_html=True)

# === EMERGENCY BUTTON ===
st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)

st.markdown("""
<div class="emergency-btn-container">
    <div class="emergency-label">🚨 ENVOYER UNE ALERTE D'URGENCE</div>
</div>
""", unsafe_allow_html=True)

_, center, _ = st.columns([1, 1, 1])
with center:
    if st.button("SEND\nALERT", key="main_alert_btn", type="primary"):
        st.switch_page("pages/client.py")

st.markdown("""
<style>
    [data-testid="stButton"] > button[kind="primary"] {
        width: 240px !important;
        height: 240px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 35% 35%, #ff6b6b, #cc0000, #880000) !important;
        color: white !important;
        font-size: 1.6rem !important;
        font-weight: 900 !important;
        border: 4px solid #ff9999 !important;
        box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7) !important;
        animation: neonPulse 2s infinite !important;
        letter-spacing: 3px;
        line-height: 1.3 !important;
        white-space: pre-line !important;
        display: block;
        margin: 0 auto;
    }
    [data-testid="stButton"] > button[kind="primary"]:hover {
        transform: scale(1.08) !important;
        background: radial-gradient(circle at 35% 35%, #ff8888, #dd0000, #bb0000) !important;
    }
</style>
""", unsafe_allow_html=True)

# === FEATURES ===
st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
st.subheader("Comment ca marche")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">📍</div>
        <div class="feature-title">Geolocalisation Auto</div>
        <div class="feature-desc">Votre position GPS est capturee automatiquement avec une precision de metres</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Alerte Instantanee</div>
        <div class="feature-desc">Un seul clic suffit pour notifier la police. Temps de transmission : 2 secondes</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🗺️</div>
        <div class="feature-title">Suivi Temps Reel</div>
        <div class="feature-desc">Les forces de l'ordre visualisent votre position sur carte avec itineraire optimise</div>
    </div>
    """, unsafe_allow_html=True)

# === POLICE ACCESS (Hidden) ===
if 'show_pin_input' not in st.session_state:
    st.session_state.show_pin_input = False

# Fixed position trigger - bottom right, very subtle
st.markdown("""
<style>
    .police-lock {
        position: fixed;
        bottom: 12px;
        right: 12px;
        z-index: 9999;
        background: rgba(10,10,20,0.8);
        border: 1px solid #222;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 0.65rem;
        color: #444;
        cursor: pointer;
        transition: all 0.3s;
        font-family: monospace;
    }
    .police-lock:hover {
        color: #666;
        border-color: #333;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

# Bottom right trigger using columns
ft1, ft2, ft3 = st.columns([6, 1, 1])
with ft3:
    if st.button("🔒", key="secure_trigger", help="Acces reserve"):
        st.session_state.show_pin_input = True
        st.rerun()

if st.session_state.show_pin_input:
    st.markdown("""
    <div style='max-width:400px; margin:0 auto 2rem auto; background:#0a0a14; border:1px solid #1a1a3a; border-radius:12px; padding:1.5rem; text-align:center;'>
    """, unsafe_allow_html=True)
    st.markdown("<h4 style='color:#4B8BFF; margin-top:0;'>🔐 Acces Forces de l'Ordre</h4>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:0.85rem;'>Code d'acces requis</p>", unsafe_allow_html=True)
    
    pin_input = st.text_input("", type="password", placeholder="PIN", key="pin_field", label_visibility="collapsed")
    
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Annuler", use_container_width=True):
            st.session_state.show_pin_input = False
            st.rerun()
    with b2:
        if st.button("Verifier", type="primary", use_container_width=True):
            if pin_input == "POLICE2026":
                st.session_state.show_pin_input = False
                st.switch_page("pages/police.py")
            else:
                st.error("Code incorrect")
    st.markdown("</div>", unsafe_allow_html=True)

# === FOOTER ===
st.markdown("""
<div class="footer-co">
    <b>MutuAlert</b> &copy; 2026 | Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> | Tous droits reserves<br>
    <span style="color:#333;">Securite civique en temps reel | POESAM 2026</span>
</div>
""", unsafe_allow_html=True)
