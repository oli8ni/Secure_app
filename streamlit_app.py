import streamlit as st

st.set_page_config(
    page_title="MutuAlert - Alertes Citoyennes",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-ring {
        0% { transform: scale(0.85); opacity: 1; }
        70% { transform: scale(1.4); opacity: 0; }
        100% { transform: scale(1.4); opacity: 0; }
    }
    @keyframes neon-glow {
        0%, 100% { text-shadow: 0 0 10px rgba(255,75,75,0.4), 0 0 20px rgba(255,0,0,0.2); }
        50% { text-shadow: 0 0 20px rgba(255,75,75,0.8), 0 0 40px rgba(255,0,0,0.4), 0 0 60px rgba(255,0,0,0.2); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF0000 40%, #CC0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        animation: neon-glow 3s ease-in-out infinite;
        letter-spacing: 4px;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #777;
        text-align: center;
        margin-bottom: 2.5rem;
        letter-spacing: 4px;
        text-transform: uppercase;
    }
    .hero-desc {
        text-align: center;
        color: #bbb;
        font-size: 1.05rem;
        max-width: 550px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.7;
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
    }
    .stat-red { color: #FF4B4B; }
    .stat-blue { color: #4B8BFF; }
    .stat-green { color: #00AA88; }
    .stat-label {
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
    .footer-co {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #0a0a0a;
        border-top: 1px solid #1a1a1a;
        padding: 0.5rem 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 100;
        font-size: 0.7rem;
        color: #555;
    }
    .footer-co a { color: #555; text-decoration: none; }
    .footer-co a:hover { color: #FF4B4B; }
    .police-trigger {
        background: none;
        border: none;
        color: #333;
        font-size: 0.7rem;
        cursor: pointer;
        padding: 0.2rem 0.5rem;
        transition: color 0.3s;
    }
    .police-trigger:hover { color: #666; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stBottom"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🛡️ MUTU ALERT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Protection civique en temps reel</div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-desc">
    <b>MutuAlert</b> connecte instantanement les citoyens en danger avec les forces de l'ordre 
    via geolocalisation precise et suivi d'itineraires en temps reel. 
    Un clic, une alerte, une reponse.
</div>
""", unsafe_allow_html=True)

st.divider()

# Main citizen button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div style='text-align:center; margin-bottom:1rem; color:#FF4B4B; font-weight:bold; letter-spacing:3px; font-size:0.85rem;'>🚨 ENVOYER UNE ALERTE</div>", unsafe_allow_html=True)
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
        animation: pulse-ring 2s infinite !important;
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
    st.markdown(f'<div class="stat-card"><div class="stat-value stat-red">{active}</div><div class="stat-label">Alertes Actives</div></div>', unsafe_allow_html=True)
with col_s2:
    total = sum(stats.values())
    st.markdown(f'<div class="stat-card"><div class="stat-value stat-red">{total}</div><div class="stat-label">Total 24h</div></div>', unsafe_allow_html=True)
with col_s3:
    st.markdown(f'<div class="stat-card"><div class="stat-value stat-blue">4.2</div><div class="stat-label">Min Response</div></div>', unsafe_allow_html=True)
with col_s4:
    st.markdown(f'<div class="stat-card"><div class="stat-value stat-green">12</div><div class="stat-label">Districts</div></div>', unsafe_allow_html=True)

# Push content above fixed footer
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

# === PIN MODAL ===
if 'show_pin_input' not in st.session_state:
    st.session_state.show_pin_input = False

if st.session_state.show_pin_input:
    st.markdown("<div style='max-width:400px; margin:0 auto 2rem auto; background:#0d0d1a; border:1px solid #333; border-radius:12px; padding:1.5rem; text-align:center;'>", unsafe_allow_html=True)
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

# === FIXED FOOTER with hidden police trigger ===
footer_html = """
<div class="footer-co">
    <div>Powered by <a href="https://www.coitechs.com" target="_blank">C&O Itech Solution</a> &copy; 2026 - Tous droits reserves</div>
    <div style="display:flex; align-items:center; gap:0.5rem;">
        <span>🔒</span>
        <span>Securise</span>
    </div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

# Hidden police trigger - bottom right area above footer
st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
ft_col1, ft_col2, ft_col3 = st.columns([5, 1, 5])
with ft_col3:
    if st.button("🔒", key="secure_trigger", help="Acces reserve aux forces de l'ordre"):
        st.session_state.show_pin_input = True
        st.rerun()
