import numpy as np

def validate_coordinates(lat, lon):
    """Validate GPS coordinates - rejects null island (0,0)"""
    try:
        lat = float(lat)
        lon = float(lon)
        # Reject 0,0 (null island / not set)
        if abs(lat) < 0.001 and abs(lon) < 0.001:
            return False
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False

def get_location_display(lat, lon):
    """Format coordinates for display"""
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    return f"{abs(lat):.6f}° {lat_dir}, {abs(lon):.6f}° {lon_dir}"

def generate_route_points(start_lat, start_lon, end_lat, end_lon, num_points=20):
    """Generate intermediate points for route visualization"""
    lats = np.linspace(start_lat, end_lat, num_points)
    lons = np.linspace(start_lon, end_lon, num_points)
    # Add slight randomness for realism
    noise_lat = np.random.normal(0, 0.0005, num_points)
    noise_lon = np.random.normal(0, 0.0005, num_points)
    return [(lats[i] + noise_lat[i], lons[i] + noise_lon[i]) for i in range(num_points)]

def estimate_response_time(distance_km):
    """Estimate police response time based on distance"""
    if distance_km < 1:
        return "2-4 min"
    elif distance_km < 3:
        return "5-8 min"
    elif distance_km < 5:
        return "8-12 min"
    elif distance_km < 10:
        return "12-20 min"
    else:
        return "20+ min"
