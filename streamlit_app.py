import streamlit as st

st.set_page_config(
    page_title="SecureAlert - Sécurite Civique",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.4); }
        70% { box-shadow: 0 0 0 20px rgba(255, 75, 75, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
    }
    @keyframes glow-text {
        0%, 100% { text-shadow: 0 0 10px rgba(255,75,75,0.5); }
        50% { text-shadow: 0 0 25px rgba(255,75,75,0.9), 0 0 40px rgba(255,0,0,0.4); }
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF0000 50%, #CC0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        animation: glow-text 3s ease-in-out infinite;
        letter-spacing: 2px;
    }
    .hero-sub {
        font-size: 1.2rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    .hero-desc {
        text-align: center;
        color: #bbb;
        font-size: 1.05rem;
        max-width: 600px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }
    .pulse-btn-wrapper {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    .pulse-btn {
        width: 220px !important;
        height: 220px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 35% 35%, #ff6b6b, #cc0000, #990000) !important;
        color: white !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        border: 4px solid #ff9999 !important;
        animation: pulse-red 2s infinite !important;
        cursor: pointer !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .pulse-btn:hover {
        transform: scale(1.05) !important;
        background: radial-gradient(circle at 35% 35%, #ff8888, #dd0000, #bb0000) !important;
    }
    .stat-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        transition: all 0.3s;
    }
    .stat-card:hover {
        border-color: #FF4B4B;
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(255,75,75,0.1);
    }
    .stat-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #FF4B4B;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .secure-footer {
        text-align: center;
        color: #444;
        font-size: 0.75rem;
        margin-top: 4rem;
        padding-top: 1rem;
        border-top: 1px solid #222;
    }
    .secure-footer a {
        color: #444;
        text-decoration: none;
    }
    .secure-footer a:hover {
        color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🛡️ SECURE ALERT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Protection civique en temps reel</div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-desc">
    Une solution technologique d'urgence qui connecte instantanement les citoyens 
    en danger avec les forces de l'ordre via geolocalisation precise et suivi d'itineraires en temps reel.
</div>
""", unsafe_allow_html=True)

st.divider()

# Main citizen button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div style='text-align:center; margin-bottom:1rem; color:#FF4B4B; font-weight:bold;'>🚨 BOUTON D'URGENCE</div>", unsafe_allow_html=True)
    if st.button("SEND ALERT", key="main_alert_btn", type="primary", use_container_width=False):
        st.switch_page("pages/client.py")

st.markdown("""
<style>
    [data-testid="stButton"] > button[kind="primary"] {
        width: 220px !important;
        height: 220px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 35% 35%, #ff6b6b, #cc0000, #990000) !important;
        color: white !important;
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        border: 4px solid #ff9999 !important;
        box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7) !important;
        animation: pulse-red 2s infinite !important;
        letter-spacing: 2px;
        margin: 0 auto;
        display: block;
    }
    [data-testid="stButton"] > button[kind="primary"]:hover {
        transform: scale(1.08) !important;
        background: radial-gradient(circle at 35% 35%, #ff8888, #dd0000, #bb0000) !important;
    }
</style>
""", unsafe_allow_html=True)

st.divider()
st.subheader("📊 Tableau de bord public")

from app.modules.database import init_db, get_alert_stats
init_db()
stats = get_alert_stats()

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    active = stats.get('active', 0)
    st.markdown(f'<div class="stat-card"><div class="stat-value">{active}</div><div class="stat-label">Alertes Actives</div></div>', unsafe_allow_html=True)
with col_s2:
    total = sum(stats.values())
    st.markdown(f'<div class="stat-card"><div class="stat-value">{total}</div><div class="stat-label">Total 24h</div></div>', unsafe_allow_html=True)
with col_s3:
    st.markdown(f'<div class="stat-card"><div class="stat-value" style="color:#4B8BFF;">4.2</div><div class="stat-label">Min Response</div></div>', unsafe_allow_html=True)
with col_s4:
    st.markdown(f'<div class="stat-card"><div class="stat-value" style="color:#00AA88;">12</div><div class="stat-label">Districts</div></div>', unsafe_allow_html=True)

st.divider()

# Police access - hidden behind PIN
st.markdown("---")

if 'show_pin_input' not in st.session_state:
    st.session_state.show_pin_input = False

# Small hidden trigger in footer area
st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)

ft_col1, ft_col2, ft_col3 = st.columns([3, 1, 3])
with ft_col2:
    if st.button("🔒 Acces securise", key="secure_trigger", help="Acces reserve aux forces de l'ordre"):
        st.session_state.show_pin_input = True
        st.rerun()

if st.session_state.show_pin_input:
    st.markdown("<div style='max-width:400px; margin:0 auto; background:#0d0d1a; border:1px solid #333; border-radius:12px; padding:1.5rem; text-align:center;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#4B8BFF; margin-top:0;'>🔐 Acces Forces de l'Ordre</h4>", unsafe_allow_html=True)
    st.markdown("<p style='color:#888; font-size:0.9rem;'>Entrez le code d'acces pour continuer</p>", unsafe_allow_html=True)
    
    pin_input = st.text_input("Code d'acces", type="password", placeholder="Code PIN", key="pin_field", label_visibility="collapsed")
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Annuler", use_container_width=True):
            st.session_state.show_pin_input = False
            st.rerun()
    with btn_col2:
        if st.button("Verifier", type="primary", use_container_width=True):
            if pin_input == "POLICE2026":
                st.session_state.show_pin_input = False
                st.session_state.police_authorized = True
                st.switch_page("pages/police.py")
            else:
                st.error("Code incorrect. Acces refuse.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div class="secure-footer">
    SecureAlert &copy; 2026 | Projet candidat au POESAM Orange | Technologies: Python, Streamlit, Folium, GPS<br>
    <span style="color:#333;">🔒 Donnees chiffrees et securisees</span>
</div>
""", unsafe_allow_html=True)
