from django.contrib import admin
from .models import ModerationLog

@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ('event', 'action', 'admin', 'reason_or_note', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('event__title', 'admin__email', 'reason_or_note')
    readonly_fields = ('event', 'admin', 'action', 'reason_or_note', 'created_at')
