import bcrypt
import streamlit as st

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def authenticate_user(username: str, password: str):
    """Authenticate police user"""
    from app.modules.database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM police_users WHERE username = ? AND is_active = 1",
            (username,)
        )
        user = cursor.fetchone()
    
    if user and verify_password(password, user['password_hash']):
        # Update last login
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE police_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            conn.commit()
        return dict(user)
    return None

def login_required():
    """Decorator to require login for police pages"""
    if 'police_user' not in st.session_state or st.session_state.police_user is None:
        st.warning("Accès réservé. Veuillez vous connecter.")
        return False
    return True

def logout():
    """Clear session"""
    if 'police_user' in st.session_state:
        st.session_state.police_user = None
    if 'auth_status' in st.session_state:
        st.session_state.auth_status = None

def get_current_user():
    return st.session_state.get('police_user')
