"""In-app notification history, FCM devices, and delivery attempts."""

from django.db import models

from apps.accounts.models import User
from apps.budgets.models import CategoryBudget
from apps.expenses.models import Expense
from apps.payments.models import Payment
from common.db_fields import (
    AsciiBinaryCollationField,
    DatabaseNowDateTime3Field,
    DateTime3Field,
    PublicIdField,
    UnsignedBigAutoField,
    UnsignedTinyIntegerField,
)


class UserDevice(models.Model):
    class Platform(models.TextChoices):
        WEB = "web", "Web"
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    fcm_token = AsciiBinaryCollationField(max_length=512, unique=True)
    platform = models.CharField(max_length=7, choices=Platform.choices)
    device_label = models.CharField(max_length=120, null=True, blank=True)
    app_version = models.CharField(max_length=30, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = DatabaseNowDateTime3Field()
    invalidated_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "user_devices"
        indexes = [models.Index(fields=("user", "is_active"), name="idx_device_user_active")]


class Notification(models.Model):
    class Type(models.TextChoices):
        BUDGET_THRESHOLD = "budget_threshold", "Budget threshold"
        BUDGET_EXCEEDED = "budget_exceeded", "Budget exceeded"
        BUDGET_UPDATED = "budget_updated", "Budget updated"
        PAYMENT_SUCCESS = "payment_success", "Payment success"
        PAYMENT_FAILED = "payment_failed", "Payment failed"
        PAYMENT_ATTENTION = "payment_attention", "Payment attention"
        SYSTEM = "system", "System"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=18, choices=Type.choices)
    severity = models.CharField(max_length=7, choices=Severity.choices, default=Severity.INFO)
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=500, null=True, blank=True)
    deep_link = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    category_budget = models.ForeignKey(
        CategoryBudget,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    dedupe_key = models.CharField(max_length=120, null=True, blank=True)
    read_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "notifications"
        constraints = [
            models.UniqueConstraint(fields=("user", "dedupe_key"), name="uq_notif_dedupe")
        ]
        indexes = [
            models.Index(fields=("user", "created_at"), name="idx_notif_user_feed"),
            models.Index(fields=("user", "read_at", "created_at"), name="idx_notif_user_unread"),
        ]

    def __str__(self):
        return self.title


class NotificationDelivery(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        TOKEN_INVALID = "token_invalid", "Token invalid"

    id = UnsignedBigAutoField(primary_key=True)
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="deliveries"
    )
    device = models.ForeignKey(
        UserDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    fcm_message_id = models.CharField(max_length=255, null=True, blank=True)
    error_code = models.CharField(max_length=80, null=True, blank=True)
    attempts = UnsignedTinyIntegerField(default=0)
    sent_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "notification_deliveries"
        indexes = [
            models.Index(fields=("notification",), name="idx_deliv_notification"),
            models.Index(fields=("status", "created_at"), name="idx_deliv_retry"),
        ]
