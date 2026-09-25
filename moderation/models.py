import uuid
from django.db import models
from django.conf import settings

class ModerationLog(models.Model):
    """
    Auditable log of every admin action taken on submissions or reports.
    """
    ACTION_APPROVE = 'APPROVE'
    ACTION_REJECT = 'REJECT'
    ACTION_STATUS_CHANGE = 'STATUS_CHANGE'
    ACTION_REPORT_RESOLVE = 'REPORT_RESOLVE'
    ACTION_REPORT_DISMISS = 'REPORT_DISMISS'

    ACTION_CHOICES = [
        (ACTION_APPROVE, 'Approved Submission'),
        (ACTION_REJECT, 'Rejected Submission'),
        (ACTION_STATUS_CHANGE, 'Status Changed'),
        (ACTION_REPORT_RESOLVE, 'Report Resolved'),
        (ACTION_REPORT_DISMISS, 'Report Dismissed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('food.FreeFoodEvent', on_delete=models.CASCADE, related_name='moderation_logs')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='moderation_actions')
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    reason_or_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_action_display()}] {self.event.title} by {self.admin} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
