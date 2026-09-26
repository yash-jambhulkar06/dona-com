from django.urls import path
from . import views

app_name = 'food'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('food/', views.event_list_view, name='event_list'),
    path('food/nearby/', views.nearby_events_view, name='nearby_events'),
    path('food/add/', views.event_add_view, name='event_add'),
    path('food/surplus-recovery/', views.surplus_recovery_feed_view, name='surplus_recovery'),
    path('food/<uuid:event_id>/', views.event_detail_view, name='event_detail'),
    path('food/<uuid:event_id>/live-status/', views.api_update_live_status, name='api_live_status'),
    path('food/<uuid:event_id>/claim-rescue/', views.claim_food_rescue_view, name='claim_food_rescue'),
    path('food/<uuid:event_id>/favorite/', views.event_favorite_toggle_api, name='event_favorite_toggle'),
    path('food/<uuid:event_id>/report/', views.event_report_api, name='event_report'),
    path('my-submissions/', views.my_submissions_view, name='my_submissions'),
    path('favorites/', views.favorites_list_view, name='favorites'),
]
