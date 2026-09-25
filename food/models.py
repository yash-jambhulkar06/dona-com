import uuid
from datetime import datetime, date
from django.db import models
from django.conf import settings
from django.utils import timezone

class FreeFoodEvent(models.Model):
    """
    Core Free-Food Event listing submitted by community members.
    Must be approved by an administrator before becoming publicly visible.
    """
    EVENT_TYPES = [
        ('Mahaprasad', 'Mahaprasad'),
        ('Langar', 'Langar'),
        ('Wedding', 'Wedding'),
        ('Religious Event', 'Religious Event'),
        ('NGO Distribution', 'NGO Food Distribution'),
        ('Community Event', 'Community Program'),
        ('Birthday', 'Birthday Celebration'),
        ('Public Distribution', 'Public Food Distribution'),
        ('Other', 'Other Free Food Event'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved & Public'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="e.g. Temple Mahaprasad, Community Langar")
    description = models.TextField(help_text="Provide context, event purpose, organizer details, etc.")
    event_type = models.CharField(max_length=64, choices=EVENT_TYPES, db_index=True)
    food_details = models.TextField(help_text="Describe food items, veg/non-veg, packaging, special instructions")
    
    event_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    venue_name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    admin_note = models.TextField(blank=True, default='', help_text="Feedback or rejection reason from admin")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_events'
    )

    class Meta:
        verbose_name = 'Free Food Event'
        verbose_name_plural = 'Free Food Events'
        ordering = ['event_date', 'start_time']
        indexes = [
            models.Index(fields=['status', 'event_date']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()}) - {self.event_date}"

    def is_expired(self) -> bool:
        """Determines if the event has already concluded based on current local time."""
        now = timezone.localtime()
        if self.event_date < now.date():
            return True
        if self.event_date == now.date() and self.end_time < now.time():
            return True
        return False

    def is_active_now(self) -> bool:
        """Checks if food is actively available right now."""
        now = timezone.localtime()
        return (
            self.status == self.STATUS_APPROVED
            and self.event_date == now.date()
            and self.start_time <= now.time() <= self.end_time
        )

    def is_starting_soon(self) -> bool:
        """Checks if the event starts within the next 60 minutes today."""
        now = timezone.localtime()
        if self.status != self.STATUS_APPROVED or self.event_date != now.date():
            return False
        if self.start_time > now.time():
            start_dt = datetime.combine(now.date(), self.start_time)
            now_dt = datetime.combine(now.date(), now.time())
            diff_seconds = (start_dt - now_dt).total_seconds()
            return 0 < diff_seconds <= 3600
        return False

    @property
    def availability_status(self) -> dict:
        """Returns visual status information for template rendering."""
        if self.status != self.STATUS_APPROVED:
            return {'label': self.get_status_display(), 'css_class': 'badge-warning' if self.status == self.STATUS_PENDING else 'badge-danger'}
        if self.is_expired():
            return {'label': 'Expired', 'css_class': 'badge-expired'}
        if self.is_active_now():
            return {'label': 'Available Now', 'css_class': 'badge-success'}
        if self.is_starting_soon():
            return {'label': 'Starts Soon', 'css_class': 'badge-warning'}
        return {'label': 'Upcoming', 'css_class': 'badge-info'}


class Favorite(models.Model):
    """Stores favorite events for authenticated users."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    event = models.ForeignKey(FreeFoodEvent, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} -> {self.event.title}"


class Report(models.Model):
    """Stores community reports for incorrect, outdated, or misleading listings."""
    REASON_WRONG_LOCATION = 'WRONG_LOCATION'
    REASON_NOT_EXIST = 'NOT_EXIST'
    REASON_EVENT_OVER = 'EVENT_OVER'
    REASON_INCORRECT_INFO = 'INCORRECT_INFO'
    REASON_MISLEADING = 'MISLEADING'
    REASON_OTHER = 'OTHER'

    REPORT_REASONS = [
        (REASON_WRONG_LOCATION, 'Wrong location or map pin'),
        (REASON_NOT_EXIST, 'Event does not exist'),
        (REASON_EVENT_OVER, 'Event is already over'),
        (REASON_INCORRECT_INFO, 'Incorrect food or timing information'),
        (REASON_MISLEADING, 'Misleading or inappropriate listing'),
        (REASON_OTHER, 'Other issue'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_REVIEWED = 'REVIEWED'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_DISMISSED = 'DISMISSED'

    REPORT_STATUSES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_REVIEWED, 'Reviewed'),
        (STATUS_RESOLVED, 'Resolved (Listing Modified/Removed)'),
        (STATUS_DISMISSED, 'Dismissed (False Report)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    event = models.ForeignKey(FreeFoodEvent, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=64, choices=REPORT_REASONS)
    details = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=REPORT_STATUSES, default=STATUS_PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_reports'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.event.title} by {self.reported_by} ({self.get_reason_display()})"
