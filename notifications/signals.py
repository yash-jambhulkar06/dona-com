import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from food.models import FreeFoodEvent, Report
from .services import send_notification, notify_admins, notify_broadcast, notify_favorites_subscribers

logger = logging.getLogger(__name__)

@receiver(post_save, sender=FreeFoodEvent)
def handle_event_post_save(sender, instance, created, **kwargs):
    """
    Handles notifications when a food event is created or updated.
    """
    try:
        if created:
            # 1. Notify Submitter that submission was received
            if instance.submitted_by:
                send_notification(
                    recipient=instance.submitted_by,
                    title="Event Submission Received",
                    message=f"Your event '{instance.title}' has been submitted and is currently pending moderator review.",
                    notification_type="NEW_SUBMISSION",
                    target_url=f"/food/{instance.id}/",
                    related_event=instance
                )

            # 2. Notify all Admins / Staff that a new submission is waiting in queue
            submitter_name = instance.submitted_by.full_name if instance.submitted_by else "A community user"
            notify_admins(
                title="New Event Awaiting Review",
                message=f"'{instance.title}' at {instance.venue_name} was submitted by {submitter_name}.",
                notification_type="NEW_SUBMISSION",
                target_url=f"/admin/food/{instance.id}/",
                related_event=instance
            )
    except Exception as e:
        logger.error(f"Error in handle_event_post_save: {e}")


@receiver(post_save, sender=Report)
def handle_report_post_save(sender, instance, created, **kwargs):
    """
    Handles notifications when a community report is filed or resolved.
    """
    try:
        if created:
            # Notify admins of new report
            reporter_name = instance.reported_by.full_name if instance.reported_by else "A user"
            notify_admins(
                title="New Listing Report",
                message=f"{reporter_name} reported '{instance.event.title}': {instance.get_reason_display()}.",
                notification_type="NEW_REPORT",
                target_url=f"/admin/reports/",
                related_event=instance.event
            )
        else:
            # When report status is updated, notify reporter
            if instance.status in [Report.STATUS_RESOLVED, Report.STATUS_DISMISSED] and instance.reported_by:
                status_text = "resolved and necessary action taken" if instance.status == Report.STATUS_RESOLVED else "reviewed by moderators"
                send_notification(
                    recipient=instance.reported_by,
                    title="Report Status Update",
                    message=f"Your report on '{instance.event.title}' has been {status_text}.",
                    notification_type="REPORT_RESOLVED",
                    target_url=f"/food/{instance.event.id}/",
                    related_event=instance.event
                )
    except Exception as e:
        logger.error(f"Error in handle_report_post_save: {e}")
