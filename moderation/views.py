from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q
from food.models import FreeFoodEvent, Report
from .models import ModerationLog
from .decorators import admin_required

@admin_required
def moderation_dashboard_view(request):
    """Admin moderation dashboard showing overview metrics and quick action items."""
    pending_count = FreeFoodEvent.objects.filter(status=FreeFoodEvent.STATUS_PENDING).count()
    approved_count = FreeFoodEvent.objects.filter(status=FreeFoodEvent.STATUS_APPROVED).count()
    rejected_count = FreeFoodEvent.objects.filter(status=FreeFoodEvent.STATUS_REJECTED).count()
    pending_reports_count = Report.objects.filter(status=Report.STATUS_PENDING).count()
    
    recent_pending = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_PENDING
    ).order_by('-created_at')[:5]
    
    recent_logs = ModerationLog.objects.select_related('event', 'admin').order_by('-created_at')[:10]
    
    return render(request, 'moderation/dashboard.html', {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_reports_count': pending_reports_count,
        'recent_pending': recent_pending,
        'recent_logs': recent_logs,
    })

@admin_required
def pending_queue_view(request):
    """Listing queue of all pending submissions awaiting admin review."""
    pending_events = FreeFoodEvent.objects.filter(
        status=FreeFoodEvent.STATUS_PENDING
    ).select_related('submitted_by').order_by('created_at')
    
    return render(request, 'moderation/pending_list.html', {
        'events': pending_events,
    })

@admin_required
def event_review_detail_view(request, event_id):
    """Full detail view for an admin to review a submission before approving or rejecting."""
    event = get_object_or_404(FreeFoodEvent.objects.select_related('submitted_by', 'approved_by'), pk=event_id)
    logs = event.moderation_logs.select_related('admin').order_by('-created_at')
    
    return render(request, 'moderation/event_review.html', {
        'event': event,
        'logs': logs,
    })

@admin_required
@require_POST
def event_approve_action(request, event_id):
    """Action to approve a submission, making it publicly discoverable."""
    event = get_object_or_404(FreeFoodEvent.objects.select_related('submitted_by'), pk=event_id)
    admin_note = request.POST.get('admin_note', '').strip()
    verify_organizer = request.POST.get('verify_organizer') in ('1', 'true', 'on')
    organizer_type = request.POST.get('organizer_type', '').strip()
    organization_name = request.POST.get('organization_name', '').strip()
    
    event.status = FreeFoodEvent.STATUS_APPROVED
    event.approved_at = timezone.now()
    event.approved_by = request.user
    if admin_note:
        event.admin_note = admin_note

    # Verified Organizer Badge Support (Future Scope Item 2)
    update_fields = ['status', 'approved_at', 'approved_by', 'admin_note', 'updated_at']
    if verify_organizer:
        event.is_verified_organizer = True
        event.organizer_type = organizer_type or 'NGO'
        event.organization_name = organization_name
        update_fields.extend(['is_verified_organizer', 'organizer_type', 'organization_name'])
        
        # Also mark the submitter's profile as a verified organizer
        if event.submitted_by:
            event.submitted_by.is_verified_organizer = True
            event.submitted_by.organizer_type = organizer_type or 'NGO'
            if organization_name:
                event.submitted_by.organization_name = organization_name
            event.submitted_by.save(update_fields=['is_verified_organizer', 'organizer_type', 'organization_name'])

    event.save(update_fields=update_fields)
    
    ModerationLog.objects.create(
        event=event,
        admin=request.user,
        action=ModerationLog.ACTION_APPROVE,
        reason_or_note=admin_note or f"Event approved for public listing. Verified Badge: {'Yes' if event.is_verified_organizer else 'No'}"
    )
    
    # Real-Time Notifications & 5 km Proximity Push Alerts (Future Scope Item 3)
    try:
        from notifications.services import send_notification, notify_broadcast, notify_proximity_subscribers
        if event.submitted_by:
            send_notification(
                recipient=event.submitted_by,
                title="Event Approved & Live!",
                message=f"Congratulations! Your event '{event.title}' has been approved by admin and is now publicly visible.",
                notification_type="EVENT_APPROVED",
                target_url=f"/food/{event.id}/",
                related_event=event
            )
        notify_broadcast(
            title=f"Free Food: {event.title}",
            message=f"{event.get_event_type_display()} at {event.venue_name} on {event.event_date}. Tap to view details and directions!",
            notification_type="EVENT_APPROVED",
            target_url=f"/food/{event.id}/",
            related_event=event
        )
        # Dispatch 5 km browser push notifications to nearby subscribers
        notify_proximity_subscribers(event, max_radius_km=5.0)
    except Exception as e:
        pass

    messages.success(request, f"Event '{event.title}' approved successfully and is now publicly visible.")
    return redirect('moderation:pending_queue')

@admin_required
@require_POST
def event_reject_action(request, event_id):
    """Action to reject a submission with an mandatory reason/feedback."""
    event = get_object_or_404(FreeFoodEvent, pk=event_id)
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    
    if not rejection_reason:
        messages.error(request, "A reason must be provided when rejecting a submission.")
        return redirect('moderation:event_review', event_id=event.id)
        
    event.status = FreeFoodEvent.STATUS_REJECTED
    event.admin_note = rejection_reason
    event.save(update_fields=['status', 'admin_note', 'updated_at'])
    
    ModerationLog.objects.create(
        event=event,
        admin=request.user,
        action=ModerationLog.ACTION_REJECT,
        reason_or_note=rejection_reason
    )
    
    # Real-Time Notification: Submitter
    try:
        from notifications.services import send_notification
        if event.submitted_by:
            send_notification(
                recipient=event.submitted_by,
                title="Submission Update: Not Approved",
                message=f"Your event '{event.title}' was reviewed. Reason: {rejection_reason}",
                notification_type="EVENT_REJECTED",
                target_url=f"/food/{event.id}/",
                related_event=event
            )
    except Exception as e:
        pass

    messages.warning(request, f"Event '{event.title}' has been rejected.")
    return redirect('moderation:pending_queue')

@admin_required
def reports_list_view(request):
    """Queue of community reports on listings."""
    status_filter = request.GET.get('status', 'PENDING')
    reports = Report.objects.select_related('event', 'reported_by', 'reviewed_by').all()
    
    if status_filter:
        reports = reports.filter(status=status_filter)
        
    reports = reports.order_by('-created_at')
    
    return render(request, 'moderation/reports_list.html', {
        'reports': reports,
        'current_status': status_filter,
    })

@admin_required
@require_POST
def report_action_view(request, report_id):
    """Take action on an individual report (Resolve, Dismiss, or Unpublish)."""
    report = get_object_or_404(Report, pk=report_id)
    action = request.POST.get('action')
    note = request.POST.get('note', '').strip()
    
    if action == 'resolve':
        report.status = Report.STATUS_RESOLVED
        msg = "Report resolved."
    elif action == 'dismiss':
        report.status = Report.STATUS_DISMISSED
        msg = "Report dismissed as invalid."
    elif action == 'unpublish':
        report.status = Report.STATUS_RESOLVED
        # Also reject/cancel the event
        report.event.status = FreeFoodEvent.STATUS_REJECTED
        report.event.admin_note = f"Removed due to report: {report.get_reason_display()} ({note})"
        report.event.save()
        ModerationLog.objects.create(
            event=report.event,
            admin=request.user,
            action=ModerationLog.ACTION_STATUS_CHANGE,
            reason_or_note=f"Listing unpublished due to community report: {note}"
        )
        msg = "Listing removed and report resolved."
    else:
        messages.error(request, "Invalid action requested.")
        return redirect('moderation:reports_list')
        
    report.reviewed_at = timezone.now()
    report.reviewed_by = request.user
    report.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
    
    # Real-Time Notifications
    try:
        from notifications.services import send_notification
        if report.reported_by:
            send_notification(
                recipient=report.reported_by,
                title="Report Status Update",
                message=f"Your report on '{report.event.title}' was reviewed: {msg}",
                notification_type="REPORT_RESOLVED",
                target_url=f"/food/{report.event.id}/",
                related_event=report.event
            )
        if action == 'unpublish' and report.event.submitted_by:
            send_notification(
                recipient=report.event.submitted_by,
                title="Listing Unpublished",
                message=f"Your event '{report.event.title}' was unpublished following a community report review.",
                notification_type="EVENT_REJECTED",
                target_url=f"/food/{report.event.id}/",
                related_event=report.event
            )
    except Exception as e:
        pass

    messages.success(request, msg)
    return redirect('moderation:reports_list')
