from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Real-Time Notifications'

    def ready(self):
        try:
            import notifications.signals  # noqa
        except ImportError:
            pass
