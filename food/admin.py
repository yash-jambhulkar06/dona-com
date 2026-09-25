from django.contrib import admin
from .models import FreeFoodEvent, Favorite, Report

@admin.register(FreeFoodEvent)
class FreeFoodEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'event_date', 'start_time', 'end_time', 'venue_name', 'status', 'submitted_by', 'created_at')
    list_filter = ('status', 'event_type', 'event_date')
    search_fields = ('title', 'venue_name', 'address', 'food_details')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'approved_by')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created_at')
    search_fields = ('user__email', 'user__mobile', 'event__title')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('event', 'reason', 'reported_by', 'status', 'created_at')
    list_filter = ('status', 'reason')
    search_fields = ('event__title', 'reported_by__email', 'details')
