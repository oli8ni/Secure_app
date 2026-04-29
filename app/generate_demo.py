import json

# Demo data generator for testing
def generate_demo_alerts():
    from modules.database import create_alert, init_db, get_db
    import random
    from datetime import datetime, timedelta
    
    init_db()
    
    demo_locations = [
        # Format: (lat, lon, type, desc)
        (48.8566, 2.3522, 'danger', 'Agression en cours, aide rapide nécessaire'),
        (48.8589, 2.3470, 'medical', 'Personne inconsciente, besoin ambulance'),
        (48.8530, 2.3490, 'suspicious', 'Groupe suspect, comportement agressif'),
        (48.8600, 2.3400, 'fire', 'Début incendie immeuble'),
        (48.8550, 2.3600, 'danger', 'Vol à main armée en cours'),
        (48.8520, 2.3300, 'medical', 'Accident de la route, blessés'),
        (48.8570, 2.3550, 'other', 'Bruit de coups, dispute violente'),
    ]
    
    for lat, lon, alert_type, desc in demo_locations:
        # Add small random offset
        lat += random.uniform(-0.003, 0.003)
        lon += random.uniform(-0.003, 0.003)
        create_alert(
            alert_type=alert_type,
            latitude=lat,
            longitude=lon,
            description=desc,
            phone=f"+225 0{random.randint(10000000, 99999999)}",
            device_id=f"demo-device-{random.randint(1000, 9999)}"
        )
    
    print(f"Generated {len(demo_locations)} demo alerts")

if __name__ == "__main__":
    generate_demo_alerts()
