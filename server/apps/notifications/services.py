"""Notification creation, inbox updates, and delivery scheduling."""

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import UserSettings
from apps.notifications.models import Notification, UserDevice


PREFERENCE_FIELDS = {
    "budget": "notify_budget_alerts",
    "payment": "notify_payment_updates",
    "system": "notify_system",
}


def _dispatch_after_commit(notification_id):
    from apps.notifications.tasks import deliver_notification_task

    transaction.on_commit(
        lambda: deliver_notification_task.delay(notification_id), robust=True
    )


@transaction.atomic
def create_notification(
    user,
    *,
    notification_type,
    title,
    body="",
    severity=Notification.Severity.INFO,
    deep_link=None,
    data=None,
    payment=None,
    expense=None,
    category_budget=None,
    dedupe_key=None,
    preference="system",
):
    preference_field = PREFERENCE_FIELDS.get(preference)
    if preference_field:
        settings_obj = UserSettings.objects.filter(user=user).only(preference_field).first()
        if settings_obj is not None and not getattr(settings_obj, preference_field):
            return None
    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                type=notification_type,
                title=title,
                body=body or None,
                severity=severity,
                deep_link=deep_link,
                data=data or None,
                payment=payment,
                expense=expense,
                category_budget=category_budget,
                dedupe_key=dedupe_key,
            )
    except IntegrityError:
        if not dedupe_key:
            raise
        notification = Notification.objects.filter(user=user, dedupe_key=dedupe_key).first()
        if notification is not None:
            _dispatch_after_commit(notification.pk)
            return notification
        raise
    _dispatch_after_commit(notification.pk)
    return notification


def queue_notification_delivery(notification):
    if notification is not None:
        _dispatch_after_commit(notification.pk)


def record_payment_status_notification(payment):
    status_value = payment.status
    config = {
        "successful": (
            Notification.Type.PAYMENT_SUCCESS,
            Notification.Severity.SUCCESS,
            "Payment completed",
            f"Your payment of {payment.amount_paise:,} paise to {payment.payee_name} was verified.",
        ),
        "failed": (
            Notification.Type.PAYMENT_FAILED,
            Notification.Severity.ERROR,
            "Payment failed",
            payment.failure_reason or f"Your payment to {payment.payee_name} failed.",
        ),
        "cancelled": (
            Notification.Type.PAYMENT_FAILED,
            Notification.Severity.INFO,
            "Payment cancelled",
            f"Your payment to {payment.payee_name} was cancelled.",
        ),
        "unknown": (
            Notification.Type.PAYMENT_ATTENTION,
            Notification.Severity.WARNING,
            "Payment needs review",
            f"Check your payment app or bank statement for the payment to {payment.payee_name}.",
        ),
    }
    values = config.get(status_value)
    if values is None:
        return None
    notification_type, severity, title, body = values
    return create_notification(
        payment.user,
        notification_type=notification_type,
        severity=severity,
        title=title,
        body=body,
        deep_link=f"/payments/{payment.public_id}",
        data={"payment_public_id": str(payment.public_id), "status": status_value},
        payment=payment,
        dedupe_key=f"payment:{payment.public_id}:{status_value}",
        preference="payment",
    )


def record_budget_updated(user, *, period_month, limit_paise, category_budget=None, category=None):
    scope = f"{category.name} category" if category is not None else "Monthly"
    return create_notification(
        user,
        notification_type=Notification.Type.BUDGET_UPDATED,
        severity=Notification.Severity.INFO,
        title=f"{scope} budget updated",
        body=f"Your {scope.lower()} budget for {period_month:%B %Y} is {limit_paise:,} paise.",
        deep_link="/budgets",
        data={
            "period_month": period_month.isoformat(),
            "limit_paise": limit_paise,
            "category_public_id": str(category.public_id) if category is not None else None,
        },
        category_budget=category_budget,
        preference="budget",
    )


@transaction.atomic
def mark_notification_read(user, public_id, *, is_read=True):
    notification = Notification.objects.filter(user=user, public_id=public_id).first()
    if notification is None:
        from rest_framework.exceptions import NotFound

        raise NotFound("Notification was not found.")
    notification.read_at = timezone.now() if is_read else None
    notification.save(update_fields=("read_at",))
    return notification


def mark_all_notifications_read(user):
    return Notification.objects.filter(user=user, read_at__isnull=True).update(read_at=timezone.now())


@transaction.atomic
def register_device(user, values):
    token = values["fcm_token"]
    device = UserDevice.objects.filter(fcm_token=token).first()
    if device is None:
        try:
            with transaction.atomic():
                device = UserDevice.objects.create(
                    user=user,
                    fcm_token=token,
                    platform=values["platform"],
                    device_label=values.get("device_label") or None,
                    app_version=values.get("app_version") or None,
                    is_active=True,
                    invalidated_at=None,
                    last_seen_at=timezone.now(),
                )
            return device
        except IntegrityError:
            device = UserDevice.objects.select_for_update().filter(fcm_token=token).first()
            if device is None:
                raise
    device.user = user
    device.platform = values["platform"]
    device.device_label = values.get("device_label") or None
    device.app_version = values.get("app_version") or None
    device.is_active = True
    device.invalidated_at = None
    device.last_seen_at = timezone.now()
    device.save(update_fields=("user", "platform", "device_label", "app_version", "is_active", "invalidated_at", "last_seen_at"))
    return device


def unregister_device(user, token):
    return UserDevice.objects.filter(user=user, fcm_token=token, is_active=True).update(
        is_active=False, invalidated_at=timezone.now()
    )
