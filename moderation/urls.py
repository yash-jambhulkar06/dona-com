from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.moderation_dashboard_view, name='dashboard'),
    path('food/pending/', views.pending_queue_view, name='pending_queue'),
    path('food/<uuid:event_id>/', views.event_review_detail_view, name='event_review'),
    path('food/<uuid:event_id>/approve/', views.event_approve_action, name='event_approve'),
    path('food/<uuid:event_id>/reject/', views.event_reject_action, name='event_reject'),
    path('reports/', views.reports_list_view, name='reports_list'),
    path('reports/<uuid:report_id>/action/', views.report_action_view, name='report_action'),
]
