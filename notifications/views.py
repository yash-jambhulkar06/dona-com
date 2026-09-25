import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator

from .models import Notification
from .services import (
    get_user_notifications,
    get_unread_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    send_notification,
    notify_admins,
    notify_broadcast
)

def api_get_notifications(request):
    """
    Real-time polling endpoint for mobile HUD banners and notification drawer.
    Supports delta syncing using `since` ISO datetime string.
    """
    since_str = request.GET.get('since')
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    limit = min(int(request.GET.get('limit', 20)), 50)

    since_dt = None
    if since_str:
        since_dt = parse_datetime(since_str)

    notifications_qs = get_user_notifications(
        user=request.user,
        limit=limit,
        unread_only=unread_only,
        since=since_dt
    )

    notifications_data = [
        n.to_dict(current_user=request.user)
        for n in notifications_qs
    ]

    unread_cnt = get_unread_count(request.user)

    return JsonResponse({
        'status': 'success',
        'unread_count': unread_cnt,
        'count': len(notifications_data),
        'notifications': notifications_data,
        'server_time': timezone.now().isoformat(),
    })


def api_unread_count(request):
    """
    Ultra-lightweight ping for unread notification count badge.
    """
    return JsonResponse({
        'status': 'success',
        'unread_count': get_unread_count(request.user),
        'server_time': timezone.now().isoformat(),
    })


@csrf_exempt
@require_POST
def api_mark_read(request, notification_id):
    """
    Marks a single notification as read.
    """
    success = mark_notification_as_read(request.user, notification_id)
    return JsonResponse({
        'status': 'success' if success else 'not_found',
        'unread_count': get_unread_count(request.user)
    })


@csrf_exempt
@require_POST
def api_mark_all_read(request):
    """
    Marks all notifications for current user as read.
    """
    marked = mark_all_notifications_as_read(request.user)
    return JsonResponse({
        'status': 'success',
        'marked_count': marked,
        'unread_count': get_unread_count(request.user)
    })


@csrf_exempt
@require_POST
def api_clear_all(request):
    """
    Clears all notifications for current user:
    Deletes personal notifications and marks broadcasts as read.
    """
    if request.user.is_authenticated:
        Notification.objects.filter(recipient=request.user).delete()
        mark_all_notifications_as_read(request.user)

    return JsonResponse({
        'status': 'success',
        'message': 'All notifications cleared.',
        'unread_count': get_unread_count(request.user)
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_test_notification(request):
    """
    Demo / Testing endpoint: Triggers an instant real-time notification
    so the user can immediately experience the mobile push banner, sound chime,
    and vibration!
    """
    is_staff = request.user.is_authenticated and request.user.is_staff

    if is_staff:
        title = "New Free Food Submission Awaiting Review"
        message = "Community Langar at Gurudwara Sahib was just submitted by Harpreet Singh. Review and approve now."
        n_type = "NEW_SUBMISSION"
        target_url = "/admin/food/pending/"
        notif = send_notification(
            recipient=request.user,
            title=title,
            message=message,
            notification_type=n_type,
            target_url=target_url
        )
    elif request.user.is_authenticated:
        title = "Mahaprasad Distribution Live Now!"
        message = "Fresh hot Mahaprasad is currently being served at Ram Mandir Hall (1.2 km away). Tap to view directions!"
        n_type = "EVENT_LIVE"
        target_url = "/food/"
        notif = send_notification(
            recipient=request.user,
            title=title,
            message=message,
            notification_type=n_type,
            target_url=target_url
        )
    else:
        # Broadcast test for visitors
        title = "Community Free Food Alert!"
        message = "Fresh food distribution has started nearby at City Central Center. Discover active events now!"
        n_type = "EVENT_NEARBY"
        target_url = "/food/"
        notif = notify_broadcast(
            title=title,
            message=message,
            notification_type=n_type,
            target_url=target_url
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json' or request.method == 'POST':
        return JsonResponse({
            'status': 'success',
            'message': 'Test real-time notification created!',
            'notification': notif.to_dict(current_user=request.user) if notif else None,
            'unread_count': get_unread_count(request.user)
        })

    return redirect('notifications:list_page')


def notification_list_page(request):
    """
    Dedicated notifications view page for full mobile and desktop history.
    """
    all_notifs = get_user_notifications(user=request.user, limit=100)
    unread_cnt = get_unread_count(request.user)

    paginator = Paginator(all_notifs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/notification_list.html', {
        'page_obj': page_obj,
        'unread_count': unread_cnt,
        'total_count': len(all_notifs),
    })
