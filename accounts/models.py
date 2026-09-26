import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with UUID primary key.
    Uses Email and Password for simple authentication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    mobile = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_image = models.URLField(max_length=500, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Verified Organizer Badge Support
    ORGANIZER_TYPE_CHOICES = [
        ('NGO', 'Registered NGO / Non-Profit'),
        ('COMMUNITY_KITCHEN', 'Community Kitchen / Langar Seva'),
        ('RELIGIOUS_TRUST', 'Religious Trust / Temple / Gurudwara / Mosque / Church'),
        ('INDIVIDUAL', 'Community Contributor'),
    ]
    is_verified_organizer = models.BooleanField(default=False, db_index=True)
    organizer_type = models.CharField(max_length=50, blank=True, choices=ORGANIZER_TYPE_CHOICES)
    organization_name = models.CharField(max_length=255, blank=True)
    
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email or str(self.id)

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else (self.email or 'Community Member')

    @property
    def organizer_badge_label(self):
        if not self.is_verified_organizer:
            return None
        labels = {
            'NGO': 'Verified NGO',
            'COMMUNITY_KITCHEN': 'Verified Community Kitchen',
            'RELIGIOUS_TRUST': 'Verified Religious Trust',
            'INDIVIDUAL': 'Verified Organizer',
        }
        return labels.get(self.organizer_type, 'Verified Organizer')
