from datetime import datetime


def get_alert_color(alert_type):
    """Couleur associée à chaque type d'alerte."""
    colors = {
        'danger':     '#FF0000',
        'medical':    '#FF8800',
        'fire':       '#FF4400',
        'suspicious': '#FFAA00',
        'other':      '#FF0088',
    }
    return colors.get(alert_type, '#FF0000')


def get_alert_icon(alert_type):
    """Icône FontAwesome associée à chaque type d'alerte."""
    icons = {
        'danger':     'exclamation',
        'medical':    'plus',
        'fire':       'fire',
        'suspicious': 'eye',
        'other':      'question',
    }
    return icons.get(alert_type, 'exclamation')


def get_alert_label(alert_type):
    """Libellé français de chaque type d'alerte."""
    labels = {
        'danger':     'DANGER VITAL',
        'medical':    'URGENCE MÉDICALE',
        'fire':       'INCENDIE',
        'suspicious': 'ACTIVITÉ SUSPECTE',
        'other':      'AUTRE ALERTE',
    }
    return labels.get(alert_type, 'ALERTE')


def format_time_ago(timestamp_str):
    """Convertit un timestamp ISO en texte relatif (ex: '5min', '2h', '1j')."""
    try:
        dt   = datetime.strptime(str(timestamp_str), '%Y-%m-%d %H:%M:%S')
        diff = datetime.now() - dt
        if diff.days > 0:
            return f"{diff.days}j"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}min"
        return "à l'instant"
    except Exception:
        return str(timestamp_str)


def create_blinking_marker_css():
    """CSS pour les marqueurs clignotants sur la carte Folium."""
    return """
    <style>
    @keyframes blink {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.3; transform: scale(1.3); }
    }
    .blinking-marker { animation: blink 1s infinite; }

    @keyframes pulsate {
        0%   { transform: scale(0.1); opacity: 1; }
        50%  { opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
    }
    .pulse-ring {
        border: 3px solid #FF0000;
        border-radius: 50%;
        height: 40px; width: 40px;
        position: absolute;
        left: -20px; top: -20px;
        animation: pulsate 2s ease-out infinite;
        opacity: 0;
    }
    </style>
    """
