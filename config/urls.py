"""
URL configuration for Community Free-Food Discovery Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from food import views as food_views

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

    # Progressive Web App (PWA) Root Endpoints
    path('sw.js', food_views.service_worker_view, name='pwa_service_worker'),
    path('manifest.json', food_views.manifest_view, name='pwa_manifest'),
    path('offline/', food_views.offline_view, name='pwa_offline'),

    # Real-Time Notifications
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
