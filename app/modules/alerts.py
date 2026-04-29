import json
import time
from modules.database import get_db

def get_alert_color(alert_type):
    """Color mapping for alert types"""
    colors = {
        'danger': '#FF0000',
        'medical': '#FF8800', 
        'fire': '#FF4400',
        'suspicious': '#FFAA00',
        'other': '#FF0088'
    }
    return colors.get(alert_type, '#FF0000')

def get_alert_icon(alert_type):
    """Icon mapping for alert types"""
    icons = {
        'danger': 'exclamation',
        'medical': 'plus',
        'fire': 'fire',
        'suspicious': 'eye',
        'other': 'question'
    }
    return icons.get(alert_type, 'exclamation')

def get_alert_label(alert_type):
    """French labels for alert types"""
    labels = {
        'danger': 'DANGER VITAL',
        'medical': 'URGENCE MÉDICALE',
        'fire': 'INCENDIE',
        'suspicious': 'ACTIVITÉ SUSPECTE',
        'other': 'AUTRE ALERTE'
    }
    return labels.get(alert_type, 'ALERTE')

def format_time_ago(timestamp_str):
    """Format timestamp as time ago"""
    from datetime import datetime
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        diff = datetime.now() - dt
        if diff.days > 0:
            return f"{diff.days}j ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}min ago"
        return "now"
    except:
        return timestamp_str

def create_blinking_marker_js():
    """JavaScript/CSS for blinking markers on map"""
    return """
    <style>
    @keyframes blink {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.3; transform: scale(1.3); }
        100% { opacity: 1; transform: scale(1); }
    }
    .blinking-marker {
        animation: blink 1s infinite;
    }
    .pulse-ring {
        border: 3px solid #FF0000;
        border-radius: 50%;
        height: 40px;
        width: 40px;
        position: absolute;
        left: -20px;
        top: -20px;
        animation: pulsate 2s ease-out infinite;
        opacity: 0;
    }
    @keyframes pulsate {
        0% { transform: scale(0.1); opacity: 1; }
        50% { opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
    }
    </style>
    """
