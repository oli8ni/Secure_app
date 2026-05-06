import bcrypt
import streamlit as st


def hash_password(password: str) -> str:
    """Génère un hash bcrypt sécurisé pour le mot de passe donné."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash bcrypt."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def authenticate_user(username: str, password: str):
    """
    Authentifie un agent de police.

    Returns:
        dict — données de l'agent si les credentials sont valides
        None — sinon
    """
    from app.modules.database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM police_users WHERE username = ? AND is_active = 1",
            (username,)
        )
        user = cursor.fetchone()

    if user and verify_password(password, user['password_hash']):
        # Mise à jour de la date de dernière connexion
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
    """
    Vérifie que l'utilisateur est connecté.
    À appeler en début de chaque page protégée.
    """
    if 'police_user' not in st.session_state or st.session_state.police_user is None:
        st.warning("Accès réservé. Veuillez vous connecter.")
        return False
    return True


def logout():
    """Déconnecte l'agent et nettoie la session."""
    st.session_state.pop('police_user', None)
    st.session_state.pop('auth_status', None)


def get_current_user():
    """Retourne l'agent connecté ou None."""
    return st.session_state.get('police_user')
