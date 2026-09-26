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
    
    # Dietary Preferences & Allergen Indicators (Future Scope Item 4)
    DIETARY_TYPES = [
        ('PURE_VEG', 'Pure Vegetarian'),
        ('VEGAN', 'Vegan (Plant-Based)'),
        ('JAIN', 'Jain Food (No Root Veg / Garlic)'),
        ('HALAL', 'Halal Prepared'),
        ('VEG_NONVEG', 'Vegetarian & Non-Vegetarian'),
        ('OTHER', 'Other / Mixed'),
    ]
    dietary_type = models.CharField(
        max_length=50,
        choices=DIETARY_TYPES,
        default='PURE_VEG',
        db_index=True,
        help_text="Dietary suitability filter"
    )
    allergens_info = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Allergen notices, e.g. Nut-Free, Gluten-Free, Dairy-Free"
    )

    # Verified Organizer Badge Support (Future Scope Item 2)
    is_verified_organizer = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Verified mark for recognized NGOs, community kitchens, or religious trusts"
    )
    organizer_type = models.CharField(max_length=50, blank=True, default='')
    organization_name = models.CharField(max_length=255, blank=True, default='')

    # Surplus Food Recovery Integration (Future Scope Item 5)
    RESCUE_STATUS_AVAILABLE = 'AVAILABLE'
    RESCUE_STATUS_IN_PROGRESS = 'IN_PROGRESS'
    RESCUE_STATUS_COMPLETED = 'COMPLETED'
    RESCUE_STATUS_CHOICES = [
        (RESCUE_STATUS_AVAILABLE, 'Available for Rescue Pickup'),
        (RESCUE_STATUS_IN_PROGRESS, 'Pickup Claimed / In Progress'),
        (RESCUE_STATUS_COMPLETED, 'Rescued & Distributed'),
    ]
    is_surplus_food = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag for excess celebration food available for volunteer food rescue pickup"
    )
    surplus_quantity = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text="Estimated surplus quantity, e.g. 50+ meals, 3 large vessels"
    )
    rescue_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        help_text="Direct phone number for pickup coordinator"
    )
    rescue_status = models.CharField(
        max_length=30,
        choices=RESCUE_STATUS_CHOICES,
        default=RESCUE_STATUS_AVAILABLE,
        db_index=True
    )

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
    def has_verified_organizer(self) -> bool:
        """Determines if the event or its submitter has an official verified badge."""
        if self.is_verified_organizer:
            return True
        if self.submitted_by and getattr(self.submitted_by, 'is_verified_organizer', False):
            return True
        return False

    @property
    def verified_organizer_badge(self) -> dict:
        """Returns details for rendering the verified badge in templates."""
        org_type = self.organizer_type or (self.submitted_by.organizer_type if self.submitted_by else '')
        org_name = self.organization_name or (self.submitted_by.organization_name if self.submitted_by else '')

        labels = {
            'NGO': 'Verified NGO',
            'COMMUNITY_KITCHEN': 'Verified Community Kitchen',
            'RELIGIOUS_TRUST': 'Verified Religious Trust',
            'INDIVIDUAL': 'Verified Organizer',
        }
        badge_label = labels.get(org_type, 'Verified Organizer')
        return {
            'is_verified': self.has_verified_organizer,
            'label': badge_label,
            'name': org_name,
            'type': org_type,
        }

    @property
    def dietary_badge_info(self) -> dict:
        """Returns visual styling and label for the dietary preference."""
        configs = {
            'PURE_VEG': {'label': 'Pure Vegetarian', 'css_class': 'badge-veg', 'symbol': 'VEG'},
            'VEGAN': {'label': 'Vegan', 'css_class': 'badge-vegan', 'symbol': 'VEGAN'},
            'JAIN': {'label': 'Jain Food', 'css_class': 'badge-jain', 'symbol': 'JAIN'},
            'HALAL': {'label': 'Halal', 'css_class': 'badge-halal', 'symbol': 'HALAL'},
            'VEG_NONVEG': {'label': 'Veg & Non-Veg', 'css_class': 'badge-mixed', 'symbol': 'MIXED'},
            'OTHER': {'label': 'Special Dietary', 'css_class': 'badge-info', 'symbol': 'DIET'},
        }
        return configs.get(self.dietary_type, {'label': self.get_dietary_type_display(), 'css_class': 'badge-secondary', 'symbol': 'FOOD'})

    def get_community_live_status(self) -> dict:
        """
        Calculates real-time community live confirmation metrics (Future Scope Item 1).
        Aggregates reports from today / active serving window.
        """
        now = timezone.localtime()
        cutoff = now - timezone.timedelta(hours=4)
        
        recent_statuses = self.live_statuses.filter(created_at__gte=cutoff)
        serving_count = recent_statuses.filter(status='SERVING').count()
        finished_count = recent_statuses.filter(status='FINISHED').count()
        total_reports = serving_count + finished_count
        
        last_report = recent_statuses.order_by('-created_at').first()
        
        if finished_count > serving_count and finished_count >= 2:
            status_code = 'FINISHED'
            status_label = 'Community Alert: Food Finished'
            css_class = 'live-status-finished'
        elif serving_count > 0:
            status_code = 'SERVING'
            status_label = f'Community Verified: Serving Food ({serving_count})'
            css_class = 'live-status-serving'
        else:
            status_code = 'UNCONFIRMED'
            status_label = 'Awaiting Live Confirmation'
            css_class = 'live-status-pending'
            
        return {
            'status_code': status_code,
            'status_label': status_label,
            'css_class': css_class,
            'serving_count': serving_count,
            'finished_count': finished_count,
            'total_reports': total_reports,
            'last_report_time': last_report.created_at if last_report else None,
        }

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


class CommunityLiveStatus(models.Model):
    """
    Community Live Status updates (Future Scope Item 1).
    Allows visitors and authenticated users to confirm serving status in real time:
    - 'Food is currently serving'
    - 'Food finished'
    """
    STATUS_SERVING = 'SERVING'
    STATUS_FINISHED = 'FINISHED'
    STATUS_CHOICES = [
        (STATUS_SERVING, 'Food is currently serving'),
        (STATUS_FINISHED, 'Food finished / over'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(FreeFoodEvent, on_delete=models.CASCADE, related_name='live_statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_status_reports')
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True, default='', help_text="Optional quick note, e.g. line moving fast, sweets finished")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'created_at']),
            models.Index(fields=['event', 'status']),
        ]

    def __str__(self):
        return f"{self.event.title}: {self.get_status_display()} ({self.created_at.strftime('%H:%M')})"


class FoodRescueClaim(models.Model):
    """
    Surplus Food Recovery claims by volunteer food rescue networks (Future Scope Item 5).
    Facilitates immediate pickup of excess feast/event food to prevent food waste.
    """
    STATUS_CLAIMED = 'CLAIMED'
    STATUS_PICKED_UP = 'PICKED_UP'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_CLAIMED, 'Claimed - Volunteer En Route'),
        (STATUS_PICKED_UP, 'Successfully Picked Up / Distributed'),
        (STATUS_CANCELLED, 'Claim Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(FreeFoodEvent, on_delete=models.CASCADE, related_name='rescue_claims')
    claimed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rescue_claims')
    volunteer_name = models.CharField(max_length=150)
    volunteer_phone = models.CharField(max_length=30)
    organization = models.CharField(max_length=255, blank=True, default='', help_text="NGO or Volunteer Network Name")
    estimated_pickup_time = models.CharField(max_length=100, help_text="e.g. In 30 mins, 4:00 PM")
    notes = models.TextField(blank=True, default='', help_text="Vehicle details, container capacity, etc.")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_CLAIMED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rescue Claim for {self.event.title} by {self.volunteer_name} ({self.organization or 'Volunteer'})"
