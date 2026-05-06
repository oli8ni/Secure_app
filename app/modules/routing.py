import requests
import math
from typing import List, Tuple, Optional
import streamlit as st


def get_osrm_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Tuple[Optional[List[List[float]]], Optional[float], Optional[float]]:
    """
    Get real driving route from OSRM (Open Source Routing Machine).
    Uses public OSRM demo server with OpenStreetMap data.
    """
    # Validate coordinates first
    if not all(isinstance(c, (int, float)) and abs(c) > 0.001 for c in [start_lat, start_lon, end_lat, end_lon]):
        return None, None, None

    try:
        # OSRM uses {lon},{lat} format — FIX: was {lat}, now {end_lat}
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{start_lon:.6f},{start_lat:.6f};{end_lon:.6f},{end_lat:.6f}"
            f"?overview=full&geometries=geojson"
        )

        resp = requests.get(url, timeout=15, headers={"User-Agent": "MutuAlert/1.0"})
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            return None, None, None

        route = data["routes"][0]
        geometry = route.get("geometry", {})

        # GeoJSON coordinates are [lon, lat] — convert to [lat, lon] for Folium
        if geometry and geometry.get("type") == "LineString" and geometry.get("coordinates"):
            coords = geometry["coordinates"]
            if len(coords) >= 2:
                folium_points = [[coord[1], coord[0]] for coord in coords]
                distance_km = route.get("distance", 0) / 1000.0
                duration_min = route.get("duration", 0) / 60.0
                return folium_points, distance_km, duration_min

        return None, None, None

    except requests.exceptions.Timeout:
        return None, None, None
    except requests.exceptions.ConnectionError:
        return None, None, None
    except Exception:
        return None, None, None


@st.cache_data(ttl=300, show_spinner=False)
def get_osrm_route_cached(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Tuple[Optional[List[List[float]]], Optional[float], Optional[float]]:
    """Cached version for police dashboard (multiple alerts)."""
    return get_osrm_route(start_lat, start_lon, end_lat, end_lon)


def get_route_fallback(start_lat: float, start_lon: float, end_lat: float, end_lon: float, num_points: int = 50) -> Tuple[List[List[float]], float, float]:
    """
    Fallback route generator when OSRM fails.
    Uses straight line interpolation with haversine distance.
    """
    lats = [start_lat + (end_lat - start_lat) * i / (num_points - 1) for i in range(num_points)]
    lons = [start_lon + (end_lon - start_lon) * i / (num_points - 1) for i in range(num_points)]

    # Add slight curve for realism (avoid perfect straight line)
    import random
    random.seed(int(start_lat * 1000000))  # Deterministic noise
    for i in range(1, num_points - 1):
        factor = math.sin(math.pi * i / num_points) * 0.0003
        lats[i] += random.uniform(-factor, factor)
        lons[i] += random.uniform(-factor, factor)

    points = [[lats[i], lons[i]] for i in range(num_points)]

    # Haversine distance
    R = 6371  # Earth radius in km
    d_lat = math.radians(end_lat - start_lat)
    d_lon = math.radians(end_lon - start_lon)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(start_lat))
        * math.cos(math.radians(end_lat))
        * math.sin(d_lon / 2) ** 2
    )
    distance_km = 2 * R * math.asin(math.sqrt(a))

    # Urban speed: 30 km/h average for RDC cities
    duration_min = (distance_km / 30.0) * 60.0 if distance_km > 0.01 else 2.0

    return points, distance_km, duration_min


def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, use_cache: bool = False) -> Tuple[List[List[float]], float, float]:
    """
    Get best available route: OSRM real roads first, fallback straight line.
    Set use_cache=True for repeated calls (police dashboard).
    """
    if use_cache:
        osrm_result = get_osrm_route_cached(start_lat, start_lon, end_lat, end_lon)
    else:
        osrm_result = get_osrm_route(start_lat, start_lon, end_lat, end_lon)

    if osrm_result[0] is not None:
        return osrm_result

    return get_route_fallback(start_lat, start_lon, end_lat, end_lon)


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
