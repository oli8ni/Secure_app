import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "securealert.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize database with required tables"""
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
                route_data TEXT
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
        
        # Add log entry
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
        """, conn, params=(cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
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

def update_alert_status(alert_id, status, resolved_by=None):
    """Update alert status"""
    with get_db() as conn:
        cursor = conn.cursor()
        if status == 'resolved':
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
        return {row['status']: row['count'] for row in cursor.fetchall()}

def get_alert_by_id(alert_id):
    """Get single alert by ID"""
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM alerts WHERE id = ?
        """, conn, params=(alert_id,))
    return df.iloc[0] if len(df) > 0 else None
