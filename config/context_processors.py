from django.conf import settings

def platform_context(request):
    """Exposes platform configuration variables to all templates."""
    return {
        'SITE_NAME': getattr(settings, 'PLATFORM_NAME', 'Dona.Com'),
        'MAP_PROVIDER': getattr(settings, 'MAP_PROVIDER', 'leaflet'),
        'MAP_API_KEY': getattr(settings, 'MAP_API_KEY', ''),
        'IS_DEV_MODE': getattr(settings, 'DEBUG', False),
    }
