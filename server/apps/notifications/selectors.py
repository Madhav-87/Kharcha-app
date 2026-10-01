"""User-scoped notification inbox queries."""

from apps.notifications.models import Notification


def list_notifications(user, *, unread_only=False, notification_type=None):
    queryset = Notification.objects.filter(user=user).order_by("-created_at", "-pk")
    if unread_only:
        queryset = queryset.filter(read_at__isnull=True)
    if notification_type:
        queryset = queryset.filter(type=notification_type)
    return queryset


def unread_count(user):
    return Notification.objects.filter(user=user, read_at__isnull=True).count()


def list_devices(user):
    return user.devices.order_by("-last_seen_at", "-pk")
