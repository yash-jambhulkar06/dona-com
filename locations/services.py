import math
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict, Any
from django.utils import timezone
from django.db.models import Q
import requests
from food.models import FreeFoodEvent

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two coordinate pairs in kilometers
    using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in kilometers
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return round(R * c, 2)


def get_recommended_events(
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    event_type: Optional[str] = None,
    availability: Optional[str] = None,
    date_filter: Optional[str] = None,
    max_distance_km: Optional[float] = None,
    search_query: Optional[str] = None,
    dietary: Optional[str] = None,
    surplus_only: bool = False,
    verified_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    Rule-based recommendation engine for free-food discovery.
    1. Filter only APPROVED events.
    2. Exclude EXPIRED & CANCELLED events.
    3. Apply search query, dietary, surplus recovery, & attribute filters.
    4. Compute distance from user's current coordinates (if available).
    5. Rank: Available Now -> Starting Soon -> Nearby Distance -> Date/Time.
    """
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    # Step 1 & 2: Approved and not expired
    queryset = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_APPROVED
    ).exclude(
        status__in=[FreeFoodEvent.STATUS_EXPIRED, FreeFoodEvent.STATUS_CANCELLED]
    ).filter(
        Q(event_date__gt=today) |
        Q(event_date=today, end_time__gte=current_time)
    )

    # Step 3: Search filter
    if search_query:
        q = search_query.strip()
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(venue_name__icontains=q) |
            Q(address__icontains=q) |
            Q(food_details__icontains=q) |
            Q(description__icontains=q)
        )

    # Event type filter
    if event_type:
        queryset = queryset.filter(event_type=event_type)

    # Dietary Preference filter (Future Scope Item 4)
    if dietary:
        queryset = queryset.filter(dietary_type=dietary)

    # Surplus Food Recovery filter (Future Scope Item 5)
    if surplus_only:
        queryset = queryset.filter(is_surplus_food=True)

    # Verified Organizer filter (Future Scope Item 2)
    if verified_only:
        queryset = queryset.filter(
            Q(is_verified_organizer=True) |
            Q(submitted_by__is_verified_organizer=True)
        )

    # Date filter
    if date_filter == 'today':
        queryset = queryset.filter(event_date=today)
    elif date_filter == 'tomorrow':
        queryset = queryset.filter(event_date=today + timedelta(days=1))
    elif date_filter == 'this_week':
        queryset = queryset.filter(event_date__range=[today, today + timedelta(days=7)])

    # Materialize candidate list
    candidate_events = list(queryset.select_related('submitted_by'))

    results = []
    for event in candidate_events:
        is_active = event.is_active_now()
        is_soon = event.is_starting_soon()
        
        # Availability filtering
        if availability == 'now' and not is_active:
            continue
        if availability == 'soon' and not is_soon:
            continue
        if availability == 'today' and event.event_date != today:
            continue

        # Distance calculation
        dist = None
        if user_lat is not None and user_lng is not None:
            try:
                dist = haversine_distance(
                    float(user_lat), float(user_lng),
                    float(event.latitude), float(event.longitude)
                )
            except (ValueError, TypeError):
                dist = None

        # Distance radius filter
        if max_distance_km and dist is not None:
            if dist > max_distance_km:
                continue

        # Calculate Ranking Score (Lower score = higher rank)
        # Priority tiers:
        # Tier 0: Available Now (Active)
        # Tier 1: Starting Soon (< 60 min)
        # Tier 2: Later Today
        # Tier 3: Future Days
        if is_active:
            tier = 0
            tier_offset = 0
        elif is_soon:
            tier = 1
            tier_offset = 1000
        elif event.event_date == today:
            tier = 2
            tier_offset = 2000
        else:
            days_diff = (event.event_date - today).days
            tier = 3 + days_diff
            tier_offset = 3000 + (days_diff * 500)

        # In-tier sorting: Distance penalty + time difference
        distance_factor = dist if dist is not None else 50.0
        
        # Rank score
        rank_score = tier_offset + distance_factor

        results.append({
            'event': event,
            'distance_km': dist,
            'is_active_now': is_active,
            'is_starting_soon': is_soon,
            'rank_score': rank_score,
            'tier': tier,
        })

    # Sort results by rule-based rank score
    results.sort(key=lambda x: x['rank_score'])
    return results


def search_places_geocoding(query: str) -> List[Dict[str, Any]]:
    """
    Geocoding helper to search for places/cities when manual location search is used.
    Uses OpenStreetMap Nominatim with fallback.
    """
    if not query or len(query.strip()) < 2:
        return []
        
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query.strip(),
            'format': 'json',
            'limit': 5,
            'addressdetails': 1,
        }
        headers = {'User-Agent': 'CommunityFreeFoodDiscoveryApp/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [{
                'display_name': item.get('display_name'),
                'lat': float(item.get('lat')),
                'lon': float(item.get('lon')),
                'type': item.get('type')
            } for item in data]
    except Exception:
        pass
        
    return []


def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocoding helper to convert coordinates to a clean human-readable place name.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 14,
            'addressdetails': 1,
        }
        headers = {'User-Agent': 'CommunityFreeFoodDiscoveryApp/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=4)
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            place = (
                address.get('village') or 
                address.get('town') or 
                address.get('city') or 
                address.get('suburb') or 
                address.get('county') or
                data.get('display_name', '').split(',')[0]
            )
            district = address.get('county') or address.get('state_district') or address.get('state')
            if place and district and place != district:
                return f"{place}, {district}"
            return place or data.get('display_name', '').split(',')[0]
    except Exception:
        pass
    return None

