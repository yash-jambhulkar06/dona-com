from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Full page
    path('', views.notification_list_page, name='list_page'),

    # Real-Time JSON API
    path('api/list/', views.api_get_notifications, name='api_list'),
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/read/<uuid:notification_id>/', views.api_mark_read, name='api_mark_read'),
    path('api/read-all/', views.api_mark_all_read, name='api_mark_all_read'),
    path('api/clear-all/', views.api_clear_all, name='api_clear_all'),
    path('api/test/', views.api_test_notification, name='api_test'),
]
