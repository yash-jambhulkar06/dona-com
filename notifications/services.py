import logging
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Notification, NotificationRead, ProximitySubscriber

logger = logging.getLogger(__name__)
User = get_user_model()

def send_notification(recipient=None, title="", message="", notification_type="SYSTEM", target_url="/", related_event=None):
    """
    Creates and dispatches a notification.
    If recipient is None, it is a broadcast notification for all community members.
    """
    try:
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            target_url=target_url or "/",
            related_event=related_event
        )
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        return None

def notify_admins(title="", message="", notification_type="SYSTEM", target_url="/", related_event=None):
    """
    Sends targeted notifications to all staff / moderators.
    """
    try:
        admins = User.objects.filter(is_staff=True, is_active=True)
        notifications = [
            Notification(
                recipient=admin,
                title=title,
                message=message,
                notification_type=notification_type,
                target_url=target_url or "/",
                related_event=related_event
            )
            for admin in admins
        ]
        if notifications:
            return Notification.objects.bulk_create(notifications)
    except Exception as e:
        logger.error(f"Failed to notify admins: {e}")
    return []

from food.models import FreeFoodEvent

def notify_broadcast(title="", message="", notification_type="EVENT_NEARBY", target_url="/", related_event=None):
    """
    Broadcasts an announcement or new food event to community members.
    Old / expired events are not broadcasted.
    """
    if related_event:
        now = timezone.localtime()
        if related_event.event_date < now.date() or (related_event.event_date == now.date() and related_event.end_time < now.time()):
            # Event has already ended; do not broadcast
            return None
        if related_event.status in [FreeFoodEvent.STATUS_EXPIRED, FreeFoodEvent.STATUS_CANCELLED, FreeFoodEvent.STATUS_REJECTED]:
            return None

    return send_notification(
        recipient=None,
        title=title,
        message=message,
        notification_type=notification_type,
        target_url=target_url,
        related_event=related_event
    )

def notify_favorites_subscribers(event, title="", message="", notification_type="EVENT_LIVE"):
    """
    Notifies users who have favorited this specific free food event.
    """
    try:
        from food.models import Favorite
        user_ids = Favorite.objects.filter(event=event).values_list('user_id', flat=True)
        notifications = [
            Notification(
                recipient_id=uid,
                title=title,
                message=message,
                notification_type=notification_type,
                target_url=f"/food/{event.id}/",
                related_event=event
            )
            for uid in user_ids
        ]
        if notifications:
            return Notification.objects.bulk_create(notifications)
    except Exception as e:
        logger.error(f"Failed to notify favorite subscribers: {e}")
    return []

def update_proximity_subscription(user=None, session_key='', latitude=None, longitude=None, radius_km=5.0, endpoint=''):
    """
    Registers or updates a user/device location for 5 km proximity push alerts (Future Scope Item 3).
    """
    if latitude is None or longitude is None:
        return None

    try:
        sub = None
        if user and user.is_authenticated:
            sub = ProximitySubscriber.objects.filter(user=user).first()
        elif session_key:
            sub = ProximitySubscriber.objects.filter(session_key=session_key).first()

        if sub:
            sub.latitude = latitude
            sub.longitude = longitude
            sub.radius_km = radius_km
            sub.push_enabled = True
            if endpoint:
                sub.endpoint = endpoint
            if user and user.is_authenticated:
                sub.user = user
            sub.save()
            return sub
        else:
            return ProximitySubscriber.objects.create(
                user=user if (user and user.is_authenticated) else None,
                session_key=session_key or '',
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                push_enabled=True,
                endpoint=endpoint or ''
            )
    except Exception as e:
        logger.error(f"Failed to update proximity subscription: {e}")
        return None

def notify_proximity_subscribers(event, max_radius_km=5.0):
    """
    Browser Push Alerts for events published within 5 km (Future Scope Item 3).
    Calculates distance to registered subscribers and creates targeted notifications.
    """
    try:
        from locations.services import haversine_distance
        
        ev_lat = float(event.latitude)
        ev_lng = float(event.longitude)
        
        # Get active subscribers who opted into proximity push alerts
        subscribers = ProximitySubscriber.objects.filter(push_enabled=True)
        created_notifications = []
        notified_user_ids = set()

        for sub in subscribers:
            if not sub.latitude or not sub.longitude:
                continue
            dist = haversine_distance(ev_lat, ev_lng, float(sub.latitude), float(sub.longitude))
            effective_radius = min(sub.radius_km or 5.0, max_radius_km)
            
            if dist <= effective_radius:
                if sub.user and sub.user.id not in notified_user_ids:
                    notified_user_ids.add(sub.user.id)
                    title = f"Free Food Near You: {event.title}"
                    msg = f"{event.get_event_type_display()} is happening {dist} km away at {event.venue_name}. Tap to view details and live status!"
                    created_notifications.append(
                        Notification(
                            recipient=sub.user,
                            title=title,
                            message=msg,
                            notification_type="EVENT_NEARBY",
                            target_url=f"/food/{event.id}/",
                            related_event=event
                        )
                    )

        if created_notifications:
            return Notification.objects.bulk_create(created_notifications)
    except Exception as e:
        logger.error(f"Failed to notify proximity subscribers: {e}")
    return []

def get_user_notifications(user, limit=30, unread_only=False, since=None):
    """
    Retrieves notifications strictly for the authenticated user.
    Unauthenticated users receive NO notifications.
    Notifications linked to past / expired / cancelled events are filtered out.
    """
    if not user or not user.is_authenticated:
        return Notification.objects.none()

    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    # User receives their targeted notifications OR community broadcasts
    qs = Notification.objects.filter(
        Q(recipient=user) | Q(recipient__isnull=True)
    ).select_related('related_event')

    # Filter out old events:
    # 1. Event date is before today
    # 2. Event date is today and end_time has passed
    # 3. Event is EXPIRED, CANCELLED, or REJECTED
    past_event_condition = Q(
        related_event__isnull=False
    ) & (
        Q(related_event__event_date__lt=today) |
        Q(related_event__event_date=today, related_event__end_time__lt=current_time) |
        Q(related_event__status__in=[
            FreeFoodEvent.STATUS_EXPIRED,
            FreeFoodEvent.STATUS_CANCELLED,
            FreeFoodEvent.STATUS_REJECTED
        ])
    )
    qs = qs.exclude(past_event_condition)

    # General notifications older than 7 days should not be displayed
    qs = qs.filter(created_at__gte=now - timezone.timedelta(days=7))

    if since:
        qs = qs.filter(created_at__gt=since)

    # Exclude read if unread_only
    if unread_only:
        read_broadcast_ids = NotificationRead.objects.filter(user=user).values_list('notification_id', flat=True)
        qs = qs.exclude(
            Q(recipient=user, is_read=True) |
            Q(recipient__isnull=True, id__in=read_broadcast_ids)
        )

    return qs.order_by('-created_at')[:limit]

def get_unread_count(user):
    """
    Calculates exact unread count strictly for authenticated users.
    Old / expired events are excluded.
    Unauthenticated users have an unread count of 0.
    """
    if not user or not user.is_authenticated:
        return 0

    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    past_event_condition = Q(
        related_event__isnull=False
    ) & (
        Q(related_event__event_date__lt=today) |
        Q(related_event__event_date=today, related_event__end_time__lt=current_time) |
        Q(related_event__status__in=[
            FreeFoodEvent.STATUS_EXPIRED,
            FreeFoodEvent.STATUS_CANCELLED,
            FreeFoodEvent.STATUS_REJECTED
        ])
    )

    # Personal unread (within last 7 days, excluding past events)
    personal_unread = Notification.objects.filter(
        recipient=user,
        is_read=False,
        created_at__gte=now - timezone.timedelta(days=7)
    ).exclude(past_event_condition).count()

    # Broadcast unread (within last 7 days, excluding past events and already read)
    read_broadcast_ids = NotificationRead.objects.filter(user=user).values_list('notification_id', flat=True)
    broadcast_unread = Notification.objects.filter(
        recipient__isnull=True,
        created_at__gte=now - timezone.timedelta(days=7)
    ).exclude(id__in=read_broadcast_ids).exclude(past_event_condition).count()

    return personal_unread + broadcast_unread


def mark_notification_as_read(user, notification_id):
    """
    Marks a notification as read for the user.
    """
    try:
        notif = Notification.objects.get(pk=notification_id)
        if user and user.is_authenticated:
            if notif.recipient == user:
                notif.is_read = True
                notif.save(update_fields=['is_read'])
            elif notif.recipient is None:
                NotificationRead.objects.get_or_create(user=user, notification=notif)
            return True
        elif notif.recipient is None:
            # Anonymous user read
            return True
    except Notification.DoesNotExist:
        pass
    return False

def mark_all_notifications_as_read(user):
    """
    Marks all notifications (personal & broadcast) as read for the user.
    """
    if not user or not user.is_authenticated:
        return 0

    # Mark personal as read
    updated = Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

    # Mark all unread broadcast notifications
    cutoff = timezone.now() - timezone.timedelta(days=14)
    unread_broadcasts = Notification.objects.filter(
        recipient__isnull=True,
        created_at__gte=cutoff
    ).exclude(
        reads__user=user
    )
    
    new_reads = [
        NotificationRead(user=user, notification=b)
        for b in unread_broadcasts
    ]
    if new_reads:
        NotificationRead.objects.bulk_create(new_reads, ignore_conflicts=True)

    return updated + len(new_reads)
