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

from .models import FreeFoodEvent, Favorite, Report
from .forms import FreeFoodEventForm, ReportForm
from locations.services import get_recommended_events, haversine_distance

def home_view(request):
    """
    Home page introducing the platform with direct location discovery CTA,
    active and upcoming events, filters, and community submission callout.
    When unauthenticated, events remain protected behind a sign-in gate.
    """
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    
    recommended = []
    user_favorites_ids = set()

    if request.user.is_authenticated:
        recommended = get_recommended_events(
            user_lat=float(user_lat) if user_lat else None,
            user_lng=float(user_lng) if user_lng else None,
        )[:9]
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

    return render(request, 'food/home.html', {
        'recommended_results': recommended,
        'total_approved': total_approved,
        'active_now_count': active_now_count,
        'user_favorites_ids': user_favorites_ids,
        'event_types': FreeFoodEvent.EVENT_TYPES,
        'user_lat': user_lat,
        'user_lng': user_lng,
    })


@login_required
def event_list_view(request):
    """
    Search and filter directory for all approved free food events.
    Supports filtering by event type, date, availability status, and search keywords.
    """
    q = request.GET.get('q', '').strip()
    event_type = request.GET.get('type', '').strip()
    date_filter = request.GET.get('date', '').strip()
    availability = request.GET.get('availability', '').strip()
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    max_dist = request.GET.get('max_distance')

    try:
        max_dist_val = float(max_dist) if max_dist else None
    except ValueError:
        max_dist_val = None

    try:
        lat_val = float(user_lat) if user_lat else None
        lng_val = float(user_lng) if user_lng else None
    except ValueError:
        lat_val, lng_val = None, None

    results = get_recommended_events(
        user_lat=lat_val,
        user_lng=lng_val,
        event_type=event_type or None,
        availability=availability or None,
        date_filter=date_filter or None,
        max_distance_km=max_dist_val,
        search_query=q or None
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
        'selected_date': date_filter,
        'selected_availability': availability,
        'selected_max_distance': max_dist,
        'event_types': FreeFoodEvent.EVENT_TYPES,
        'user_favorites_ids': user_favorites_ids,
        'user_lat': user_lat,
        'user_lng': user_lng,
    })


@login_required
def nearby_events_view(request):
    """
    Dedicated location-centric discovery view. Requests browser coordinates
    and ranks events by distance and real-time availability.
    """
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    radius = request.GET.get('radius', '25')

    try:
        radius_val = float(radius)
    except ValueError:
        radius_val = 25.0

    results = []
    lat_val, lng_val = None, None
    if user_lat and user_lng:
        try:
            lat_val = float(user_lat)
            lng_val = float(user_lng)
            results = get_recommended_events(
                user_lat=lat_val,
                user_lng=lng_val,
                max_distance_km=radius_val
            )
        except ValueError:
            pass

    user_favorites_ids = set()
    if request.user.is_authenticated:
        user_favorites_ids = set(request.user.favorites.values_list('event_id', flat=True))

    return render(request, 'food/nearby.html', {
        'results': results,
        'has_location': bool(lat_val and lng_val),
        'user_lat': user_lat,
        'user_lng': user_lng,
        'radius': radius,
        'user_favorites_ids': user_favorites_ids,
    })


@login_required
def event_detail_view(request, event_id):
    """
    Public event detail view.
    Security: PENDING or REJECTED events are only accessible by their submitter or staff.
    """
    event = get_object_or_404(FreeFoodEvent.objects.select_related('submitted_by'), pk=event_id)
    
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
    directions_url = f"https://www.google.com/maps/dir/?api=1&destination={event.latitude},{event.longitude}"

    return render(request, 'food/event_detail.html', {
        'event': event,
        'is_favorited': is_favorited,
        'report_form': report_form,
        'directions_url': directions_url,
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
