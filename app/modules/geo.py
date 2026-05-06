import numpy as np
import requests
import math


def validate_coordinates(lat, lon):
    """Valide des coordonnées GPS — rejette l'île null (0,0)."""
    try:
        lat = float(lat)
        lon = float(lon)
        if abs(lat) < 0.001 and abs(lon) < 0.001:
            return False
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def get_location_display(lat, lon):
    """Formate les coordonnées pour l'affichage."""
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    return f"{abs(lat):.6f}° {lat_dir}, {abs(lon):.6f}° {lon_dir}"


def haversine_km(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points GPS (formule de Haversine)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi   = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def generate_route_points(start_lat, start_lon, end_lat, end_lon, num_points=30):
    """
    Génère les points d'un itinéraire entre deux coordonnées GPS.

    Stratégie :
      1. Essaie d'abord l'API OSRM (Project-OSRM public, routes réelles sur OpenStreetMap).
      2. En cas d'échec réseau ou de timeout, repasse en mode linéaire interpolé avec
         un bruit réaliste simulant les courbes de routes.

    Returns:
        list[tuple(float, float)] — liste de (latitude, longitude)
    """
    # --- Tentative avec l'API OSRM (routes réelles) ---
    try:
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{start_lon},{start_lat};{end_lon},{end_lat}"
            f"?overview=full&geometries=geojson&steps=false"
        )
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data["routes"]:
                coords = data["routes"][0]["geometry"]["coordinates"]
                # OSRM renvoie [lon, lat] → on inverse en [lat, lon]
                return [(c[1], c[0]) for c in coords]
    except Exception:
        pass  # Timeout ou pas de réseau → fallback ci-dessous

    # --- Fallback : ligne droite avec bruit naturel ---
    return _linear_route_fallback(start_lat, start_lon, end_lat, end_lon, num_points)


def _linear_route_fallback(start_lat, start_lon, end_lat, end_lon, num_points=30):
    """
    Génère un itinéraire simulé par interpolation linéaire avec légère déviation.
    Utilisé quand OSRM n'est pas disponible.
    """
    lats = np.linspace(start_lat, end_lat, num_points)
    lons = np.linspace(start_lon, end_lon, num_points)

    # Bruit progressif : plus fort au milieu du trajet (simulation des virages)
    t        = np.linspace(0, 1, num_points)
    envelope = np.sin(t * np.pi) * 0.001   # amplitude max au milieu
    noise_lat = np.random.normal(0, 1, num_points) * envelope
    noise_lon = np.random.normal(0, 1, num_points) * envelope

    return [(lats[i] + noise_lat[i], lons[i] + noise_lon[i]) for i in range(num_points)]


def estimate_response_time(distance_km):
    """Estime le temps de réponse policière selon la distance."""
    if distance_km < 1:
        return "2–4 min"
    elif distance_km < 3:
        return "5–8 min"
    elif distance_km < 5:
        return "8–12 min"
    elif distance_km < 10:
        return "12–20 min"
    else:
        return "20+ min"
