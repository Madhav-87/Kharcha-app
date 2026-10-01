"""Celery tasks for reliable per-device FCM delivery."""

import logging

from celery import shared_task
from django.utils import timezone

from apps.accounts.models import UserSettings
from apps.notifications.fcm import FCMDeliveryError, send_notification
from apps.notifications.models import Notification, NotificationDelivery, UserDevice


logger = logging.getLogger(__name__)


@shared_task(bind=True, name="notifications.deliver_notification", max_retries=5)
def deliver_notification_task(self, notification_id):
    notification = Notification.objects.filter(pk=notification_id).select_related("user").first()
    if notification is None:
        return 0
    settings_obj = UserSettings.objects.filter(user=notification.user).first()
    if settings_obj is not None and not settings_obj.push_enabled:
        return 0
    preference_for_type = {
        Notification.Type.BUDGET_THRESHOLD: "notify_budget_alerts",
        Notification.Type.BUDGET_EXCEEDED: "notify_budget_alerts",
        Notification.Type.BUDGET_UPDATED: "notify_budget_alerts",
        Notification.Type.PAYMENT_SUCCESS: "notify_payment_updates",
        Notification.Type.PAYMENT_FAILED: "notify_payment_updates",
        Notification.Type.PAYMENT_ATTENTION: "notify_payment_updates",
        Notification.Type.SYSTEM: "notify_system",
    }.get(notification.type)
    if settings_obj is not None and preference_for_type and not getattr(settings_obj, preference_for_type):
        return 0

    devices = UserDevice.objects.filter(user=notification.user, is_active=True)
    retryable_failures = []
    sent_count = 0
    for device in devices:
        if NotificationDelivery.objects.filter(
            notification=notification,
            device=device,
            status=NotificationDelivery.Status.SENT,
        ).exists():
            continue
        attempts = NotificationDelivery.objects.filter(
            notification=notification, device=device
        ).count() + 1
        delivery = NotificationDelivery.objects.create(
            notification=notification,
            device=device,
            status=NotificationDelivery.Status.QUEUED,
            attempts=min(attempts, 255),
        )
        try:
            message_id = send_notification(device, notification)
        except FCMDeliveryError as exc:
            delivery.status = (
                NotificationDelivery.Status.TOKEN_INVALID
                if exc.token_invalid
                else NotificationDelivery.Status.FAILED
            )
            delivery.error_code = exc.code
            delivery.save(update_fields=("status", "error_code"))
            if exc.token_invalid:
                device.is_active = False
                device.invalidated_at = timezone.now()
                device.save(update_fields=("is_active", "invalidated_at"))
            elif exc.retryable and attempts < 255:
                retryable_failures.append(exc)
            logger.warning("FCM delivery failed for notification %s: %s", notification.public_id, exc.code)
        else:
            delivery.status = NotificationDelivery.Status.SENT
            delivery.fcm_message_id = message_id[:255]
            delivery.sent_at = timezone.now()
            delivery.save(update_fields=("status", "fcm_message_id", "sent_at"))
            sent_count += 1

    if retryable_failures:
        delay = min(300, 2 ** min(self.request.retries + 1, 8))
        raise self.retry(exc=retryable_failures[0], countdown=delay)
    return sent_count
