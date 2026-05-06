import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "securealert.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
    """Initialise la base de données et crée toutes les tables si elles n'existent pas."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Table des alertes citoyennes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type          TEXT    NOT NULL DEFAULT 'danger',
                latitude            REAL    NOT NULL,
                longitude           REAL    NOT NULL,
                accuracy            REAL,
                description         TEXT,
                phone               TEXT,
                device_id           TEXT,
                status              TEXT    DEFAULT 'active',
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at         TIMESTAMP,
                resolved_by         TEXT,
                route_data          TEXT,
                police_station_id   INTEGER
            )
        """)

        # Table des agents de police
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS police_users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT    UNIQUE NOT NULL,
                password_hash   TEXT    NOT NULL,
                full_name       TEXT    NOT NULL,
                badge_number    TEXT    UNIQUE,
                role            TEXT    DEFAULT 'officer',
                station         TEXT,
                is_active       INTEGER DEFAULT 1,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login      TIMESTAMP
            )
        """)

        # Table des postes de police
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS police_stations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                latitude    REAL    NOT NULL,
                longitude   REAL    NOT NULL,
                address     TEXT,
                phone       TEXT,
                is_default  INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Journal d'audit (toutes les actions sur les alertes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_logs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id     INTEGER NOT NULL,
                action       TEXT    NOT NULL,
                performed_by TEXT,
                details      TEXT,
                timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts(id)
            )
        """)

        # Insertion des comptes de démo si la table est vide
        cursor.execute("SELECT COUNT(*) FROM police_users")
        if cursor.fetchone()[0] == 0:
            import bcrypt
            admin_hash   = bcrypt.hashpw("Police2026!".encode(),  bcrypt.gensalt()).decode()
            officer_hash = bcrypt.hashpw("Officer2026!".encode(), bcrypt.gensalt()).decode()
            cursor.executemany("""
                INSERT INTO police_users (username, password_hash, full_name, badge_number, role, station)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [
                ("admin",    admin_hash,   "Administrateur", "ADM001", "admin",   "Central"),
                ("officer1", officer_hash, "Agent Kabila",   "OFF001", "officer", "District 1"),
            ])

        # Insertion des postes de démo si la table est vide
        cursor.execute("SELECT COUNT(*) FROM police_stations")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO police_stations (name, latitude, longitude, address, phone, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [
                ("Commissariat Central Kinshasa", 5.3364,  15.3222, "Gombe, Kinshasa",      "+243 81 000 0001", 1),
                ("Commissariat Commune Lingwala", 5.3530,  15.3030, "Lingwala, Kinshasa",    "+243 81 000 0002", 0),
                ("Commissariat Commune Kintambo", 5.3197,  15.2897, "Kintambo, Kinshasa",   "+243 81 000 0003", 0),
            ])

        conn.commit()


@contextmanager
def get_db():
    """Gestionnaire de contexte pour les connexions SQLite."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ==================== ALERTES ====================

def create_alert(alert_type, latitude, longitude, accuracy=None,
                 description=None, phone=None, device_id=None):
    """Crée une nouvelle alerte citoyenne."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (alert_type, latitude, longitude, accuracy,
                                description, phone, device_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
        """, (alert_type, latitude, longitude, accuracy, description, phone, device_id))
        alert_id = cursor.lastrowid
        conn.commit()
        cursor.execute("""
            INSERT INTO alert_logs (alert_id, action, performed_by, details)
            VALUES (?, 'created', 'system', 'Alerte créée par le client')
        """, (alert_id,))
        conn.commit()
        return alert_id


def get_active_alerts():
    """Retourne les alertes actives des dernières 24 heures."""
    cutoff = datetime.now() - timedelta(hours=24)
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM alerts
            WHERE status = 'active'
              AND created_at > ?
            ORDER BY created_at DESC
        """, conn, params=(cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
    return df


def get_all_alerts(limit=100):
    """Retourne toutes les alertes (limitées)."""
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM alerts
            ORDER BY created_at DESC
            LIMIT ?
        """, conn, params=(limit,))
    return df


def get_alert_by_id(alert_id):
    """Retourne une alerte par son identifiant."""
    with get_db() as conn:
        df = pd.read_sql_query("SELECT * FROM alerts WHERE id = ?", conn, params=(alert_id,))
    return df.iloc[0] if len(df) > 0 else None


def update_alert_status(alert_id, status, resolved_by=None):
    """Met à jour le statut d'une alerte."""
    with get_db() as conn:
        cursor = conn.cursor()
        if status == 'resolved':
            cursor.execute("""
                UPDATE alerts
                SET status = ?, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE id = ?
            """, (status, resolved_by, alert_id))
        else:
            cursor.execute("""
                UPDATE alerts SET status = ?, resolved_by = ? WHERE id = ?
            """, (status, resolved_by, alert_id))
        conn.commit()
        cursor.execute("""
            INSERT INTO alert_logs (alert_id, action, performed_by, details)
            VALUES (?, 'status_update', ?, ?)
        """, (alert_id, resolved_by, f"Statut changé en : {status}"))
        conn.commit()


def add_route_data(alert_id, route_json, updated_by=None):
    """Sauvegarde les données de route pour une alerte."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET route_data = ? WHERE id = ?", (route_json, alert_id))
        conn.commit()
        cursor.execute("""
            INSERT INTO alert_logs (alert_id, action, performed_by, details)
            VALUES (?, 'route_added', ?, 'Données de route mises à jour')
        """, (alert_id, updated_by))
        conn.commit()


def get_alert_stats():
    """Retourne les statistiques des alertes des dernières 24 heures."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM alerts
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY status
        """)
        return {row['status']: row['count'] for row in cursor.fetchall()}


# ==================== POSTES DE POLICE ====================

def get_police_stations():
    """Retourne tous les postes de police."""
    with get_db() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM police_stations ORDER BY is_default DESC, name",
            conn
        )
    return df


def get_default_station():
    """Retourne le poste de police par défaut."""
    with get_db() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM police_stations WHERE is_default = 1 LIMIT 1",
            conn
        )
    return df.iloc[0] if len(df) > 0 else None


def get_station_by_id(station_id):
    """Retourne un poste par son identifiant."""
    with get_db() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM police_stations WHERE id = ?", conn, params=(station_id,)
        )
    return df.iloc[0] if len(df) > 0 else None


def add_police_station(name, latitude, longitude, address=None, phone=None, is_default=False):
    """Ajoute un nouveau poste de police."""
    with get_db() as conn:
        cursor = conn.cursor()
        if is_default:
            cursor.execute("UPDATE police_stations SET is_default = 0")
        cursor.execute("""
            INSERT INTO police_stations (name, latitude, longitude, address, phone, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, latitude, longitude, address, phone, 1 if is_default else 0))
        conn.commit()
        return cursor.lastrowid


def update_station_default(station_id):
    """Définit un poste comme poste actif (par défaut)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE police_stations SET is_default = 0")
        cursor.execute("UPDATE police_stations SET is_default = 1 WHERE id = ?", (station_id,))
        conn.commit()


def delete_station(station_id):
    """Supprime un poste de police."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM police_stations WHERE id = ?", (station_id,))
        conn.commit()
