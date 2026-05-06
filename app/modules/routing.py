import requests
import json
from typing import List, Tuple, Optional

def get_osrm_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Tuple[Optional[List[List[float]]], Optional[float], Optional[float]]:
    """
    Get real driving route from OSRM (Open Source Routing Machine).
    Uses public OSRM demo server with OpenStreetMap data.
    
    Args:
        start_lat, start_lon: Starting coordinates
        end_lat, end_lon: Ending coordinates
    
    Returns:
        (folium_points, distance_km, duration_min)
        folium_points: List of [lat, lon] for Folium PolyLine
        distance_km: Total distance in kilometers
        duration_min: Estimated duration in minutes
    """
    try:
        # OSRM uses {lon},{lat} format
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{lat}?overview=full&geometries=geojson"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") != "Ok":
            return None, None, None
        
        route = data["routes"][0]
        geometry = route["geometry"]
        
        # GeoJSON coordinates are [lon, lat] - convert to [lat, lon] for Folium
        if geometry.get("type") == "LineString":
            folium_points = [[coord[1], coord[0]] for coord in geometry["coordinates"]]
        else:
            # Fallback to straight line if geometry is malformed
            return None, None, None
        
        distance_km = route["distance"] / 1000.0
        duration_min = route["duration"] / 60.0
        
        return folium_points, distance_km, duration_min
    
    except Exception as e:
        print(f"OSRM routing error: {e}")
        return None, None, None


def get_route_fallback(start_lat: float, start_lon: float, end_lat: float, end_lon: float, num_points: int = 50) -> Tuple[List[List[float]], float, float]:
    """
    Fallback route generator when OSRM fails (no internet, OSRM down).
    Uses straight line interpolation with approximate distance/time.
    """
    from app.modules.geo import generate_route_points
    points = generate_route_points(start_lat, start_lon, end_lat, end_lon, num_points)
    
    # Haversine distance (approximate)
    import math
    R = 6371  # Earth radius in km
    d_lat = math.radians(end_lat - start_lat)
    d_lon = math.radians(end_lon - start_lon)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(d_lon/2)**2
    distance_km = 2 * R * math.asin(math.sqrt(a))
    
    # Assume 30 km/h average speed in urban Africa
    duration_min = (distance_km / 30.0) * 60.0
    
    return points, distance_km, duration_min


def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Tuple[List[List[float]], float, float]:
    """
    Get best available route: OSRM real roads first, fallback straight line.
    """
    osrm_result = get_osrm_route(start_lat, start_lon, end_lat, end_lon)
    if osrm_result[0] is not None:
        return osrm_result
    
    return get_route_fallback(start_lat, start_lon, end_lat, end_lon)


def get_nearest_station(lat: float, lon: float, stations_df) -> Optional[dict]:
    """Find nearest police station to given coordinates."""
    import math
    
    if stations_df is None or len(stations_df) == 0:
        return None
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    min_dist = float('inf')
    nearest = None
    for idx, row in stations_df.iterrows():
        dist = haversine(lat, lon, row['latitude'], row['longitude'])
        if dist < min_dist:
            min_dist = dist
            nearest = row
    
    return nearest
