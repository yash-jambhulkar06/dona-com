"""
URL configuration for Community Free-Food Discovery Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    
    # Custom admin moderation dashboard & queues
    path('admin/', include('moderation.urls')),
    
    # Accounts & Authentication (Login, Register, Profile, Logout)
    path('', include('accounts.urls')),
    
    # Free-Food Core (Home, Browse, Details, Add, Favorites, Reports, My Submissions)
    path('', include('food.urls')),
    
    # Locations, Maps & Geocoding
    path('', include('locations.urls')),

    # Real-Time Notifications
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
