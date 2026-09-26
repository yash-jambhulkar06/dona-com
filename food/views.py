import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from .models import FreeFoodEvent, Favorite, Report, CommunityLiveStatus, FoodRescueClaim
from .forms import FreeFoodEventForm, ReportForm, FoodRescueClaimForm
from locations.services import get_recommended_events, haversine_distance

def home_view(request):
    """
    Home page introducing the platform with direct location discovery CTA,
    active and upcoming events, filters, and community submission callout.
    Public visitors can browse approved events; authentication is only needed
    for account-specific actions such as favorites and submissions.
    """
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    dietary = request.GET.get('dietary', '').strip()
    
    user_favorites_ids = set()

    try:
        lat_val = float(user_lat) if user_lat else None
        lng_val = float(user_lng) if user_lng else None
        if lat_val is not None and not -90 <= lat_val <= 90:
            lat_val = None
        if lng_val is not None and not -180 <= lng_val <= 180:
            lng_val = None
    except ValueError:
        lat_val, lng_val = None, None

    recommended = get_recommended_events(
        user_lat=lat_val,
        user_lng=lng_val,
        dietary=dietary or None,
    )[:9]
    if request.user.is_authenticated:
        user_favorites_ids = set(request.user.favorites.values_list('event_id', flat=True))

    # Active count metrics (safe summary counters for platform transparency)
    now = timezone.localtime()
    total_approved = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_APPROVED,
        event_date__gte=now.date()
    ).count()

    active_now_count = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_APPROVED,
        event_date=now.date(),
        start_time__lte=now.time(),
        end_time__gte=now.time()
    ).count()

    surplus_count = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_APPROVED,
        is_surplus_food=True,
        rescue_status=FreeFoodEvent.RESCUE_STATUS_AVAILABLE,
        event_date__gte=now.date()
    ).count()

    return render(request, 'food/home.html', {
        'recommended_results': recommended,
        'total_approved': total_approved,
        'active_now_count': active_now_count,
        'surplus_count': surplus_count,
        'user_favorites_ids': user_favorites_ids,
        'event_types': FreeFoodEvent.EVENT_TYPES,
        'dietary_types': FreeFoodEvent.DIETARY_TYPES,
        'selected_dietary': dietary,
        'user_lat': user_lat,
        'user_lng': user_lng,
    })


def event_list_view(request):
    """
    Search and filter directory for all approved free food events.
    Supports filtering by event type, date, availability status, dietary preferences,
    surplus food recovery, verified organizers, and search keywords.
    """
    q = request.GET.get('q', '').strip()
    event_type = request.GET.get('type', '').strip()
    dietary = request.GET.get('dietary', '').strip()
    date_filter = request.GET.get('date', '').strip()
    availability = request.GET.get('availability', '').strip()
    surplus_only = request.GET.get('surplus', '').lower() in ('true', '1')
    verified_only = request.GET.get('verified', '').lower() in ('true', '1')
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    max_dist = request.GET.get('max_distance')

    try:
        max_dist_val = float(max_dist) if max_dist else None
    except ValueError:
        max_dist_val = None
    if max_dist_val is not None and max_dist_val < 0:
        max_dist_val = None

    try:
        lat_val = float(user_lat) if user_lat else None
        lng_val = float(user_lng) if user_lng else None
        if lat_val is not None and not -90 <= lat_val <= 90:
            lat_val, lng_val = None, None
        if lng_val is not None and not -180 <= lng_val <= 180:
            lat_val, lng_val = None, None
    except ValueError:
        lat_val, lng_val = None, None

    results = get_recommended_events(
        user_lat=lat_val,
        user_lng=lng_val,
        event_type=event_type or None,
        availability=availability or None,
        date_filter=date_filter or None,
        max_distance_km=max_dist_val,
        search_query=q or None,
        dietary=dietary or None,
        surplus_only=surplus_only,
        verified_only=verified_only,
    )

    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    user_favorites_ids = set()
    if request.user.is_authenticated:
        user_favorites_ids = set(request.user.favorites.values_list('event_id', flat=True))

    return render(request, 'food/event_list.html', {
        'page_obj': page_obj,
        'results_count': len(results),
        'search_query': q,
        'selected_type': event_type,
        'selected_dietary': dietary,
        'selected_surplus': surplus_only,
        'selected_verified': verified_only,
        'selected_date': date_filter,
        'selected_availability': availability,
        'selected_max_distance': max_dist,
        'event_types': FreeFoodEvent.EVENT_TYPES,
        'dietary_types': FreeFoodEvent.DIETARY_TYPES,
        'user_favorites_ids': user_favorites_ids,
        'user_lat': user_lat,
        'user_lng': user_lng,
    })


def nearby_events_view(request):
    """
    Dedicated location-centric discovery view. Requests browser coordinates
    and ranks events by distance and real-time availability.
    Also provides pins_json so an interactive map can be rendered.
    """
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    dietary = request.GET.get('dietary', '').strip()
    surplus_only = request.GET.get('surplus', '').lower() in ('true', '1')
    location_name = request.GET.get('location_name', '').strip()
    radius = request.GET.get('radius', '25')

    try:
        radius_val = float(radius)
        if radius_val <= 0:
            radius_val = 25.0
    except ValueError:
        radius_val = 25.0

    results = []
    lat_val, lng_val = None, None
    if user_lat and user_lng:
        try:
            lat_val = float(user_lat)
            lng_val = float(user_lng)
            if not (-90 <= lat_val <= 90 and -180 <= lng_val <= 180):
                raise ValueError
            results = get_recommended_events(
                user_lat=lat_val,
                user_lng=lng_val,
                max_distance_km=radius_val,
                dietary=dietary or None,
                surplus_only=surplus_only,
            )
            if not location_name:
                from locations.services import reverse_geocode
                location_name = reverse_geocode(lat_val, lng_val) or "Current Location"
        except ValueError:
            pass

    user_favorites_ids = set()
    if request.user.is_authenticated:
        user_favorites_ids = set(request.user.favorites.values_list('event_id', flat=True))

    pins = []
    for item in results:
        ev = item['event']
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
            'dietary': ev.dietary_badge_info,
            'is_verified': ev.has_verified_organizer,
            'verified_badge': ev.verified_organizer_badge,
            'is_surplus': ev.is_surplus_food,
            'detail_url': reverse('food:event_detail', kwargs={'event_id': ev.id}),
            'directions_url': directions_url,
            'distance_km': item.get('distance_km'),
        })

    return render(request, 'food/nearby.html', {
        'results': results,
        'has_location': bool(lat_val and lng_val),
        'user_lat': user_lat,
        'user_lng': user_lng,
        'dietary_types': FreeFoodEvent.DIETARY_TYPES,
        'selected_dietary': dietary,
        'selected_surplus': surplus_only,
        'location_name': location_name,
        'radius': radius,
        'user_favorites_ids': user_favorites_ids,
        'pins_json': json.dumps(pins),
    })


def event_detail_view(request, event_id):
    """
    Public event detail view.
    Security: PENDING or REJECTED events are only accessible by their submitter or staff.
    """
    event = get_object_or_404(
        FreeFoodEvent.objects.select_related('submitted_by', 'approved_by'),
        pk=event_id
    )
    
    # Access control: unapproved listings cannot be viewed by arbitrary users
    if event.status != FreeFoodEvent.STATUS_APPROVED:
        is_owner = request.user.is_authenticated and request.user == event.submitted_by
        is_admin = request.user.is_authenticated and request.user.is_staff
        if not (is_owner or is_admin):
            raise Http404("Event listing is not currently available.")

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, event=event).exists()

    report_form = ReportForm()
    claim_form = FoodRescueClaimForm()
    directions_url = f"https://www.google.com/maps/dir/?api=1&destination={event.latitude},{event.longitude}"
    canonical_url = request.build_absolute_uri(reverse('food:event_detail', kwargs={'event_id': event.id}))
    
    # Community Live Status metrics (Future Scope Item 1)
    live_status = event.get_community_live_status()

    # Surplus Food Rescue Claims (Future Scope Item 5)
    rescue_claims = event.rescue_claims.all().order_by('-created_at')

    return render(request, 'food/event_detail.html', {
        'event': event,
        'is_favorited': is_favorited,
        'report_form': report_form,
        'claim_form': claim_form,
        'live_status': live_status,
        'rescue_claims': rescue_claims,
        'directions_url': directions_url,
        'canonical_url': canonical_url,
    })


@login_required
def event_add_view(request):
    """
    Form view for authenticated users to submit a free food event.
    Upon submission, event is set to PENDING status awaiting admin review.
    """
    if request.method == 'POST':
        form = FreeFoodEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.submitted_by = request.user
            event.status = FreeFoodEvent.STATUS_PENDING
            event.save()
            messages.success(
                request,
                "Your submission has been sent for admin verification. "
                "It will be publicly visible once approved by a moderator."
            )
            return redirect('food:my_submissions')
        else:
            messages.error(request, "Please check the form for errors and required fields.")
    else:
        form = FreeFoodEventForm()

    return render(request, 'food/event_form.html', {
        'form': form,
    })


@login_required
@require_POST
def event_favorite_toggle_api(request, event_id):
    """
    AJAX endpoint to add or remove an event from user's favorites.
    Prevents duplicates.
    """
    event = get_object_or_404(FreeFoodEvent, pk=event_id)
    favorite = Favorite.objects.filter(user=request.user, event=event).first()
    
    if favorite:
        favorite.delete()
        favorited = False
        message = "Removed from your favorites."
    else:
        Favorite.objects.create(user=request.user, event=event)
        favorited = True
        message = "Added to your favorites!"
        
    return JsonResponse({
        'status': 'success',
        'favorited': favorited,
        'message': message,
        'total_favorites': request.user.favorites.count()
    })


@login_required
@require_POST
def event_report_api(request, event_id):
    """
    Submit a community report against an event listing.
    """
    event = get_object_or_404(FreeFoodEvent, pk=event_id)
    form = ReportForm(request.POST)
    
    if form.is_valid():
        report = form.save(commit=False)
        report.reported_by = request.user
        report.event = event
        report.status = Report.STATUS_PENDING
        report.save()
        messages.success(request, "Thank you. Your report has been submitted to moderators for review.")
    else:
        messages.error(request, "Unable to submit report. Please select a reason.")
        
    return redirect('food:event_detail', event_id=event.id)


@login_required
def my_submissions_view(request):
    """
    Displays the authenticated user's submission history with real-time status.
    """
    submissions = FreeFoodEvent.objects.filter(
        submitted_by=request.user
    ).order_by('-created_at')

    return render(request, 'food/my_submissions.html', {
        'submissions': submissions,
    })


@login_required
def favorites_list_view(request):
    """
    Displays the list of events favorited by the user.
    """
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('event').order_by('-created_at')

    return render(request, 'food/favorites.html', {
        'favorites': favorites,
    })


@require_POST
def api_update_live_status(request, event_id):
    """
    Real-time Community Live Status confirmation (Future Scope Item 1).
    Allows visitors and users to confirm whether food is currently serving or finished.
    Rate limited to 1 update per 30 minutes per user/session.
    """
    event = get_object_or_404(FreeFoodEvent, pk=event_id)
    status_choice = request.POST.get('status', '').strip().upper()
    note = request.POST.get('note', '').strip()[:255]

    if status_choice not in (CommunityLiveStatus.STATUS_SERVING, CommunityLiveStatus.STATUS_FINISHED):
        return JsonResponse({'status': 'error', 'message': 'Invalid status choice.'}, status=400)

    # Establish identity (user or session)
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key or ''
    ip = request.META.get('REMOTE_ADDR')

    # Rate limiting: check if this user/session reported in the last 30 minutes
    cutoff = timezone.now() - timezone.timedelta(minutes=30)
    existing_query = Q(created_at__gte=cutoff)
    if request.user.is_authenticated:
        existing_query &= (Q(user=request.user) | Q(session_key=session_key))
    else:
        existing_query &= Q(session_key=session_key)

    recent_report = event.live_statuses.filter(existing_query).first()
    if recent_report:
        recent_report.status = status_choice
        if note:
            recent_report.note = note
        recent_report.save()
        action_text = "Updated your live status confirmation!"
    else:
        CommunityLiveStatus.objects.create(
            event=event,
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key,
            ip_address=ip,
            status=status_choice,
            note=note
        )
        action_text = "Thank you! Your live status confirmation has been recorded."

    live_metrics = event.get_community_live_status()
    return JsonResponse({
        'status': 'success',
        'message': action_text,
        'live_status': {
            'status_code': live_metrics['status_code'],
            'status_label': live_metrics['status_label'],
            'css_class': live_metrics['css_class'],
            'serving_count': live_metrics['serving_count'],
            'finished_count': live_metrics['finished_count'],
            'total_reports': live_metrics['total_reports'],
        }
    })


@login_required
def surplus_recovery_feed_view(request):
    """
    Dedicated Surplus Food Recovery feed (Future Scope Item 5).
    Connects volunteer food rescue networks to prevent food waste from weddings, feasts, and community meals.
    """
    now = timezone.localtime()
    surplus_events = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_APPROVED,
        is_surplus_food=True,
        event_date__gte=now.date()
    ).exclude(
        status__in=[FreeFoodEvent.STATUS_EXPIRED, FreeFoodEvent.STATUS_CANCELLED]
    ).order_by('event_date', 'start_time')

    return render(request, 'food/surplus_recovery.html', {
        'surplus_events': surplus_events,
        'now': now,
    })


@login_required
@require_POST
def claim_food_rescue_view(request, event_id):
    """
    Claims surplus food for volunteer pickup and rescue (Future Scope Item 5).
    Updates event status and notifies the event organizer.
    """
    event = get_object_or_404(FreeFoodEvent, pk=event_id)
    form = FoodRescueClaimForm(request.POST)

    if form.is_valid():
        claim = form.save(commit=False)
        claim.event = event
        claim.claimed_by = request.user
        claim.status = FoodRescueClaim.STATUS_CLAIMED
        claim.save()

        # Update event rescue status
        event.rescue_status = FreeFoodEvent.RESCUE_STATUS_IN_PROGRESS
        event.save(update_fields=['rescue_status'])

        # Notify the original submitter that a volunteer is coming
        try:
            from notifications.services import send_notification
            if event.submitted_by:
                send_notification(
                    recipient=event.submitted_by,
                    title="Surplus Food Rescue Pickup In Progress!",
                    message=(
                        f"Volunteer {claim.volunteer_name} ({claim.organization or 'Food Rescue'}) "
                        f"has claimed your surplus food. Estimated arrival: {claim.estimated_pickup_time}. "
                        f"Contact: {claim.volunteer_phone}"
                    ),
                    notification_type="SYSTEM",
                    target_url=f"/food/{event.id}/",
                    related_event=event
                )
        except Exception:
            pass

        messages.success(
            request,
            f"Thank you for helping rescue food! Your claim for '{event.title}' has been submitted. "
            f"The organizer has been notified."
        )
    else:
        messages.error(request, "Unable to complete claim. Please check your contact information.")

    return redirect('food:event_detail', event_id=event.id)
