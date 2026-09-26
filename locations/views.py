import json
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from food.models import FreeFoodEvent
from .services import search_places_geocoding, get_recommended_events, reverse_geocode

@login_required
def map_view(request):
    """
    Interactive map view displaying all approved active and upcoming free-food events.
    Allows user to see their current position and get direct directions to any event.
    """
    now = timezone.localtime()
    events = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_APPROVED
    ).exclude(
        status__in=[FreeFoodEvent.STATUS_EXPIRED, FreeFoodEvent.STATUS_CANCELLED]
    ).filter(
        Q(event_date__gt=now.date()) |
        Q(event_date=now.date(), end_time__gte=now.time())
    )

    pins = []
    for ev in events:
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ev.latitude},{ev.longitude}"
        pins.append({
            'id': str(ev.id),
            'title': ev.title,
            'event_type': ev.get_event_type_display(),
            'venue_name': ev.venue_name,
            'address': ev.address,
            'food_details': ev.food_details,
            'lat': float(ev.latitude),
            'lng': float(ev.longitude),
            'date': ev.event_date.strftime('%b %d, %Y'),
            'time': f"{ev.start_time.strftime('%I:%M %p')} - {ev.end_time.strftime('%I:%M %p')}",
            'status': ev.availability_status,
            'detail_url': reverse('food:event_detail', kwargs={'event_id': ev.id}),
            'directions_url': directions_url,
        })

    return render(request, 'locations/map_view.html', {
        'pins_json': json.dumps(pins),
        'total_pins': len(pins),
    })

@login_required
def location_search_api(request):
    """
    AJAX endpoint for manual location search when browser geolocation is denied or unavailable.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
        
    results = search_places_geocoding(query)
    return JsonResponse({'results': results})

@login_required
def reverse_geocode_api(request):
    """
    AJAX endpoint to reverse geocode lat/lng into a clean location name.
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    if not lat or not lng:
        return JsonResponse({'name': None})
    try:
        name = reverse_geocode(float(lat), float(lng))
        return JsonResponse({'name': name})
    except (ValueError, TypeError):
        return JsonResponse({'name': None})

