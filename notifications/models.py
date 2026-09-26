import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    """
    Real-Time Mobile-App Style Notification Model.
    Supports targeted user notifications and broadcast community alerts.
    """
    TYPE_EVENT_APPROVED = 'EVENT_APPROVED'
    TYPE_EVENT_REJECTED = 'EVENT_REJECTED'
    TYPE_NEW_SUBMISSION = 'NEW_SUBMISSION'
    TYPE_NEW_REPORT = 'NEW_REPORT'
    TYPE_REPORT_RESOLVED = 'REPORT_RESOLVED'
    TYPE_EVENT_NEARBY = 'EVENT_NEARBY'
    TYPE_EVENT_LIVE = 'EVENT_LIVE'
    TYPE_SYSTEM = 'SYSTEM'

    TYPE_CHOICES = [
        (TYPE_EVENT_APPROVED, 'Event Approved'),
        (TYPE_EVENT_REJECTED, 'Event Rejected'),
        (TYPE_NEW_SUBMISSION, 'New Event Submission'),
        (TYPE_NEW_REPORT, 'Community Report'),
        (TYPE_REPORT_RESOLVED, 'Report Update'),
        (TYPE_EVENT_NEARBY, 'Free Food Near You'),
        (TYPE_EVENT_LIVE, 'Food Active Right Now'),
        (TYPE_SYSTEM, 'System Announcement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Recipient user. If null, broadcasted to all community members."
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=TYPE_SYSTEM,
        db_index=True
    )
    target_url = models.CharField(max_length=500, blank=True, default='/')
    related_event = models.ForeignKey(
        'food.FreeFoodEvent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        recip = self.recipient.email if self.recipient else "All Users"
        return f"[{self.notification_type}] {self.title} -> {recip}"

    def time_ago(self):
        """Returns human-friendly relative time string like mobile apps."""
        now = timezone.now()
        diff = now - self.created_at
        seconds = int(diff.total_seconds())
        if seconds < 45:
            return "Just now"
        elif seconds < 3600:
            m = max(1, seconds // 60)
            return f"{m}m ago"
        elif seconds < 86400:
            h = max(1, seconds // 3600)
            return f"{h}h ago"
        elif seconds < 604800:
            d = max(1, seconds // 86400)
            return f"{d}d ago"
        return self.created_at.strftime("%b %d, %Y")

    def to_dict(self, current_user=None):
        """Serializes notification for real-time mobile JSON sync."""
        is_user_read = self.is_read
        if current_user and current_user.is_authenticated:
            if self.recipient is None:
                is_user_read = self.reads.filter(user=current_user).exists()
            elif self.recipient == current_user:
                is_user_read = self.is_read

        return {
            'id': str(self.id),
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'target_url': self.target_url,
            'is_read': is_user_read,
            'created_at': self.created_at.isoformat(),
            'time_ago': self.time_ago(),
            'event_id': str(self.related_event_id) if self.related_event_id else None,
        }


class NotificationRead(models.Model):
    """
    Tracks read status of broadcast (recipient=None) notifications per user.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_reads')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'notification')
        indexes = [
            models.Index(fields=['user', 'notification']),
        ]

    def __str__(self):
        return f"{self.user} read {self.notification_id}"


class ProximitySubscriber(models.Model):
    """
    Subscribers for 5 km proximity push alerts (Future Scope Item 3).
    Stores user/device current coordinates for real-time location-based alerts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='proximity_subscriptions'
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    radius_km = models.FloatField(default=5.0, help_text="Proximity alert threshold in km (default: 5.0 km)")
    push_enabled = models.BooleanField(default=True)
    endpoint = models.CharField(max_length=500, blank=True, default='', help_text="Browser Web Push subscription endpoint or token")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'push_enabled']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        target = self.user.email if self.user else f"Session {self.session_key[:8]}"
        return f"ProximityAlert({target} at {self.latitude},{self.longitude} <= {self.radius_km}km)"
