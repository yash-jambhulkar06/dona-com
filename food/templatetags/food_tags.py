from django import template
from typing import Optional

register = template.Library()

@register.filter(name='format_distance')
def format_distance_filter(dist):
    """
    Formats distance for clean consumer display:
    - Under 1 km: '500 m away'
    - 1 km or more: '1.2 km away', '3.4 km away'
    - None / invalid: 'Search your area'
    """
    if dist is None or dist == '':
        return ''
    try:
        km = float(dist)
        if km < 0:
            return ''
        if km < 1.0:
            meters = max(10, int(round(km * 1000)))
            return f"{meters} m away"
        return f"{km:.1f} km away"
    except (ValueError, TypeError):
        return ''
