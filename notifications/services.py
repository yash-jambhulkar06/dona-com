import logging
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Notification, NotificationRead

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

def notify_broadcast(title="", message="", notification_type="EVENT_NEARBY", target_url="/", related_event=None):
    """
    Broadcasts an announcement or new food event to all community members.
    """
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

def get_user_notifications(user, limit=30, unread_only=False, since=None):
    """
    Retrieves notifications relevant to this user (personal + broadcast).
    Supports delta fetching via `since` ISO timestamp or datetime.
    """
    if user and user.is_authenticated:
        # User gets their personal notifications OR broadcast (recipient is null)
        qs = Notification.objects.filter(
            Q(recipient=user) | Q(recipient__isnull=True)
        ).select_related('related_event')
    else:
        # Anonymous visitors get public broadcast notifications
        qs = Notification.objects.filter(recipient__isnull=True).select_related('related_event')

    if since:
        qs = qs.filter(created_at__gt=since)

    # Exclude read if unread_only
    if unread_only and user and user.is_authenticated:
        # Exclude read personal notifications and read broadcast notifications
        read_broadcast_ids = NotificationRead.objects.filter(user=user).values_list('notification_id', flat=True)
        qs = qs.exclude(
            Q(recipient=user, is_read=True) |
            Q(recipient__isnull=True, id__in=read_broadcast_ids)
        )

    return qs.order_by('-created_at')[:limit]

def get_unread_count(user):
    """
    Calculates exact unread count for user in a high-performance query.
    """
    if not user or not user.is_authenticated:
        # For anonymous visitors, count broadcasts created in the last 24h
        cutoff = timezone.now() - timezone.timedelta(days=1)
        return Notification.objects.filter(recipient__isnull=True, created_at__gte=cutoff).count()

    # Personal unread
    personal_unread = Notification.objects.filter(recipient=user, is_read=False).count()

    # Broadcast unread (broadcasts that user hasn't marked read yet)
    cutoff = timezone.now() - timezone.timedelta(days=7) # last 7 days broadcast
    read_broadcast_ids = NotificationRead.objects.filter(user=user).values_list('notification_id', flat=True)
    broadcast_unread = Notification.objects.filter(
        recipient__isnull=True,
        created_at__gte=cutoff
    ).exclude(id__in=read_broadcast_ids).count()

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
