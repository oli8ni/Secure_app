import requests
import math
import random
from typing import List, Tuple, Optional, Dict


def _coords_valid(start_lat, start_lon, end_lat, end_lon):
    """Validate coordinates before routing."""
    return all(
        isinstance(c, (int, float)) and abs(c) > 0.001
        for c in [start_lat, start_lon, end_lat, end_lon]
    )


def get_osrm_multi_routes(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float, max_alternatives: int = 2
) -> List[Dict]:
    """
    Get multiple driving routes from OSRM with alternatives.
    Returns list of route dicts: [{points, distance_km, duration_min, label, color}, ...]
    OSRM alternatives=2 returns up to 2 routes for simple A->B routes.
    """
    if not _coords_valid(start_lat, start_lon, end_lat, end_lon):
        return []

    routes = []
    try:
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{start_lon:.6f},{start_lat:.6f};{end_lon:.6f},{end_lat:.6f}"
            f"?overview=full&geometries=geojson"
            f"&alternatives={max_alternatives}"
        )

        resp = requests.get(url, timeout=15, headers={"User-Agent": "MutuAlert/1.0"})
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            return []

        colors = ["#00CC88", "#4B8BFF", "#FF8800"]
        labels = ["ROUTE RAPIDE", "ROUTE ALTERNATIVE", "ROUTE DIRECTE"]

        for i, route in enumerate(data["routes"][:3]):
            geometry = route.get("geometry", {})
            if geometry and geometry.get("type") == "LineString":
                coords = geometry["coordinates"]
                if len(coords) >= 2:
                    folium_points = [[c[1], c[0]] for c in coords]
                    dist_km = route.get("distance", 0) / 1000.0
                    dur_min = route.get("duration", 0) / 60.0
                    routes.append({
                        "points": folium_points,
                        "distance_km": dist_km,
                        "duration_min": dur_min,
                        "label": labels[i] if i < len(labels) else f"ROUTE {i+1}",
                        "color": colors[i] if i < len(colors) else "#FF8800",
                        "weight": 5 if i == 0 else 3,
                        "source": "OSRM",
                    })

    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.ConnectionError:
        pass
    except Exception:
        pass

    return routes


def get_route_fallback(start_lat: float, start_lon: float, end_lat: float, end_lon: float, num_points: int = 50) -> Dict:
    """
    Fallback route when OSRM fails. Returns a single route dict.
    """
    lats = [start_lat + (end_lat - start_lat) * i / (num_points - 1) for i in range(num_points)]
    lons = [start_lon + (end_lon - start_lon) * i / (num_points - 1) for i in range(num_points)]

    # Add slight curve for realism
    random.seed(int(start_lat * 1000000))
    for i in range(1, num_points - 1):
        factor = math.sin(math.pi * i / num_points) * 0.0003
        lats[i] += random.uniform(-factor, factor)
        lons[i] += random.uniform(-factor, factor)

    points = [[lats[i], lons[i]] for i in range(num_points)]

    # Haversine distance
    R = 6371
    d_lat = math.radians(end_lat - start_lat)
    d_lon = math.radians(end_lon - start_lon)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(start_lat))
        * math.cos(math.radians(end_lat))
        * math.sin(d_lon / 2) ** 2
    )
    distance_km = 2 * R * math.asin(math.sqrt(a))
    duration_min = (distance_km / 30.0) * 60.0 if distance_km > 0.01 else 2.0

    return {
        "points": points,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "label": "ROUTE ESTIMEE (DIRECTE)",
        "color": "#FF4444",
        "weight": 3,
        "source": "FALLBACK",
        "is_fallback": True,
    }


def get_routes(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> List[Dict]:
    """
    Get best available routes. Returns 1-3 route options:
    - Primary: OSRM route rapide (green)
    - Secondary: OSRM alternative if available (blue)  
    - Fallback: Ligne directe if OSRM fails (red)
    """
    osrm_routes = get_osrm_multi_routes(start_lat, start_lon, end_lat, end_lon)

    if len(osrm_routes) >= 1:
        return osrm_routes

    # OSRM failed entirely - return single fallback
    return [get_route_fallback(start_lat, start_lon, end_lat, end_lon)]


# Legacy single-route function for backward compatibility
def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, use_cache: bool = False) -> Tuple[List[List[float]], float, float]:
    """Backward compatible single route."""
    routes = get_routes(start_lat, start_lon, end_lat, end_lon)
    if routes:
        r = routes[0]
        return r["points"], r["distance_km"], r["duration_min"]
    return [], 0.0, 0.0


def get_nearest_station(lat: float, lon: float, stations_df) -> Optional[dict]:
    """Find nearest police station to given coordinates."""
    if stations_df is None or len(stations_df) == 0:
        return None

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        return 2 * R * math.asin(math.sqrt(a))

    min_dist = float("inf")
    nearest = None
    for idx, row in stations_df.iterrows():
        dist = haversine(lat, lon, row["latitude"], row["longitude"])
        if dist < min_dist:
            min_dist = dist
            nearest = row

    return nearest
