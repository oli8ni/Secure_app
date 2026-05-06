import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "securealert.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
    """Initialize database with required tables and indexes"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL DEFAULT 'danger',
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                description TEXT,
                phone TEXT,
                device_id TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                route_data TEXT,
                police_station_id INTEGER
            )
        """)

        # Police users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS police_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                badge_number TEXT UNIQUE,
                role TEXT DEFAULT 'officer',
                station TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Police stations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS police_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                phone TEXT,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Hospitals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                phone TEXT,
                emergency INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alert logs (audit trail)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                performed_by TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts(id)
            )
        """)

        # === INDEXES FOR PERFORMANCE ===
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_status_created
            ON alerts(status, created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_created
            ON alerts(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_logs_alert_id
            ON alert_logs(alert_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_logs_timestamp
            ON alert_logs(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stations_default
            ON police_stations(is_default)
        """)

        # Insert demo police users if empty
        cursor.execute("SELECT COUNT(*) FROM police_users")
        if cursor.fetchone()[0] == 0:
            import bcrypt

            default_hash = bcrypt.hashpw("Police2026!".encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO police_users (username, password_hash, full_name, badge_number, role, station)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin", default_hash, "Administrateur", "ADM001", "admin", "Central"))

            officer_hash = bcrypt.hashpw("Officer2026!".encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO police_users (username, password_hash, full_name, badge_number, role, station)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("officer1", officer_hash, "Agent Martin", "OFF001", "officer", "District 1"))

        # Insert default police stations in RDC if empty
        cursor.execute("SELECT COUNT(*) FROM police_stations")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO police_stations (name, latitude, longitude, address, phone, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Commissariat Central Kinshasa", -4.3250, 15.3222, "Gombe, Kinshasa, RDC", "+243 81 000 0000", 1))
            cursor.execute("""
                INSERT INTO police_stations (name, latitude, longitude, address, phone, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Poste Police Kintambo", -4.3340, 15.3100, "Kintambo, Kinshasa, RDC", "+243 81 111 1111", 0))
            cursor.execute("""
                INSERT INTO police_stations (name, latitude, longitude, address, phone, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Poste Police Limete", -4.3700, 15.3500, "Limete, Kinshasa, RDC", "+243 81 222 2222", 0))

        # Insert default hospitals in RDC if empty
        cursor.execute("SELECT COUNT(*) FROM hospitals")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO hospitals (name, latitude, longitude, address, phone, emergency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Hopital du Cinquantenaire", -4.3250, 15.3120, "Gombe, Kinshasa, RDC", "+243 81 333 3333", 1))
            cursor.execute("""
                INSERT INTO hospitals (name, latitude, longitude, address, phone, emergency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Hopital General de Reference", -4.3410, 15.3200, "Kinshasa, RDC", "+243 81 444 4444", 1))

        conn.commit()


@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_alert(alert_type, latitude, longitude, accuracy=None, description=None, phone=None, device_id=None):
    """Create a new alert"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (alert_type, latitude, longitude, accuracy, description, phone, device_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
        """, (alert_type, latitude, longitude, accuracy, description, phone, device_id))
        alert_id = cursor.lastrowid
        conn.commit()

        cursor.execute("""
            INSERT INTO alert_logs (alert_id, action, performed_by, details)
            VALUES (?, 'created', 'system', 'Alert created by client')
        """, (alert_id,))
        conn.commit()
        return alert_id


def get_active_alerts():
    """Get all active alerts from last 24 hours"""
    cutoff = datetime.now() - timedelta(hours=24)
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM alerts
            WHERE status = 'active'
            AND created_at > ?
            ORDER BY created_at DESC
        """, conn, params=(cutoff.strftime("%Y-%m-%d %H:%M:%S"),))
    return df


def get_all_alerts(limit=100):
    """Get all alerts with limit"""
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM alerts
            ORDER BY created_at DESC
            LIMIT ?
        """, conn, params=(limit,))
    return df


def get_alert_by_id(alert_id):
    """Get single alert by ID"""
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM alerts WHERE id = ?
        """, conn, params=(alert_id,))
    return df.iloc[0] if len(df) > 0 else None


def update_alert_status(alert_id, status, resolved_by=None):
    """Update alert status"""
    with get_db() as conn:
        cursor = conn.cursor()
        if status == "resolved":
            cursor.execute("""
                UPDATE alerts SET status = ?, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE id = ?
            """, (status, resolved_by, alert_id))
        else:
            cursor.execute("""
                UPDATE alerts SET status = ?, resolved_by = ?
                WHERE id = ?
            """, (status, resolved_by, alert_id))
        conn.commit()

        cursor.execute("""
            INSERT INTO alert_logs (alert_id, action, performed_by, details)
            VALUES (?, 'status_update', ?, ?)
        """, (alert_id, resolved_by, f"Status changed to {status}"))
        conn.commit()


def add_route_data(alert_id, route_json, updated_by=None):
    """Store route data for an alert"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts SET route_data = ? WHERE id = ?
        """, (route_json, alert_id))
        conn.commit()

        cursor.execute("""
            INSERT INTO alert_logs (alert_id, action, performed_by, details)
            VALUES (?, 'route_added', ?, 'Route data updated')
        """, (alert_id, updated_by))
        conn.commit()


def get_alert_stats():
    """Get alert statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM alerts
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY status
        """)
        return {row["status"]: row["count"] for row in cursor.fetchall()}


# ========== POLICE STATIONS ==========


def get_police_stations():
    """Get all police stations"""
    with get_db() as conn:
        df = pd.read_sql_query("SELECT * FROM police_stations ORDER BY is_default DESC, name", conn)
    return df


def get_default_station():
    """Get default police station"""
    with get_db() as conn:
        df = pd.read_sql_query("SELECT * FROM police_stations WHERE is_default = 1 LIMIT 1", conn)
    return df.iloc[0] if len(df) > 0 else None


def get_station_by_id(station_id):
    """Get station by ID"""
    if station_id is None:
        return None
    with get_db() as conn:
        df = pd.read_sql_query("SELECT * FROM police_stations WHERE id = ?", conn, params=(station_id,))
    return df.iloc[0] if len(df) > 0 else None


def add_police_station(name, latitude, longitude, address=None, phone=None, is_default=False):
    """Add a new police station"""
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
    """Set a station as default"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE police_stations SET is_default = 0")
        cursor.execute("UPDATE police_stations SET is_default = 1 WHERE id = ?", (station_id,))
        conn.commit()


def delete_station(station_id):
    """Delete a station"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM police_stations WHERE id = ?", (station_id,))
        conn.commit()


# ========== HOSPITALS ==========


def get_hospitals():
    """Get all hospitals"""
    with get_db() as conn:
        df = pd.read_sql_query("SELECT * FROM hospitals ORDER BY name", conn)
    return df


def add_hospital(name, latitude, longitude, address=None, phone=None, emergency=True):
    """Add a new hospital"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hospitals (name, latitude, longitude, address, phone, emergency)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, latitude, longitude, address, phone, 1 if emergency else 0))
        conn.commit()
        return cursor.lastrowid


def delete_hospital(hospital_id):
    """Delete a hospital"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hospitals WHERE id = ?", (hospital_id,))
        conn.commit()


def import_stations_from_geojson(geojson_data):
    """Import police stations from GeoJSON FeatureCollection"""
    imported = 0
    if "features" not in geojson_data:
        return 0
    for feat in geojson_data["features"]:
        geom = feat.get("geometry", {})
        if geom.get("type") == "Point":
            coords = geom.get("coordinates", [0, 0])
            props = feat.get("properties", {})
            if len(coords) >= 2:
                try:
                    add_police_station(
                        name=props.get("name", f"Poste {imported+1}"),
                        latitude=float(coords[1]),
                        longitude=float(coords[0]),
                        address=props.get("address"),
                        phone=props.get("phone"),
                    )
                    imported += 1
                except Exception:
                    pass
    return imported


def import_hospitals_from_geojson(geojson_data):
    """Import hospitals from GeoJSON FeatureCollection"""
    imported = 0
    if "features" not in geojson_data:
        return 0
    for feat in geojson_data["features"]:
        geom = feat.get("geometry", {})
        if geom.get("type") == "Point":
            coords = geom.get("coordinates", [0, 0])
            props = feat.get("properties", {})
            if len(coords) >= 2:
                try:
                    add_hospital(
                        name=props.get("name", f"Hopital {imported+1}"),
                        latitude=float(coords[1]),
                        longitude=float(coords[0]),
                        address=props.get("address"),
                        phone=props.get("phone"),
                    )
                    imported += 1
                except Exception:
                    pass
    return imported
