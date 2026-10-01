"""Saved payees, UPI app metadata, payment attempts, and immutable events."""

from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    FixedCharField,
    PublicIdField,
    UnsignedBigAutoField,
    UnsignedBigIntegerField,
    UnsignedIntegerField,
    UnsignedSmallAutoField,
    UpdatedDateTime3Field,
)


class UpiApp(models.Model):
    id = UnsignedSmallAutoField(primary_key=True)
    code = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=60)
    android_package = models.CharField(max_length=120, null=True, blank=True)
    ios_scheme = models.CharField(max_length=60, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "upi_apps"

    def __str__(self):
        return self.display_name


class Payee(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payees")
    name = models.CharField(max_length=120)
    upi_id = models.CharField(max_length=100)
    default_category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        db_column="default_category_id",
        null=True,
        blank=True,
        related_name="payees",
    )
    is_favorite = models.BooleanField(default=False)
    use_count = UnsignedIntegerField(default=0)
    last_used_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "payees"
        constraints = [
            models.UniqueConstraint(fields=("user", "upi_id"), name="uq_payee_user_upi")
        ]
        indexes = [models.Index(fields=("user", "last_used_at"), name="idx_payee_recent")]

    def __str__(self):
        return self.name


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PROCESSING = "processing", "Processing"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        UNKNOWN = "unknown", "Unknown"
        CANCELLED = "cancelled", "Cancelled"

    class ConfirmedBy(models.TextChoices):
        UPI_CALLBACK = "upi_callback", "UPI callback"
        USER_MANUAL = "user_manual", "User manual"
        RECONCILIATION = "reconciliation", "Reconciliation"
        SYSTEM = "system", "System"

    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    payee = models.ForeignKey(
        Payee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    payee_name = models.CharField(max_length=120)
    payee_upi_id = models.CharField(max_length=100)
    amount_paise = UnsignedBigIntegerField()
    currency = FixedCharField(max_length=3, default="INR")
    note = models.CharField(max_length=255, null=True, blank=True)
    upi_app = models.ForeignKey(
        UpiApp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INITIATED)
    reference_code = models.CharField(max_length=40, unique=True)
    upi_txn_ref = models.CharField(max_length=80, null=True, blank=True)
    failure_reason = models.CharField(max_length=255, null=True, blank=True)
    confirmed_by = models.CharField(
        max_length=15, choices=ConfirmedBy.choices, null=True, blank=True
    )
    idempotency_key = models.CharField(max_length=80, null=True, blank=True)
    initiated_at = DatabaseNowDateTime3Field()
    redirected_at = DateTime3Field(null=True, blank=True)
    resolved_at = DateTime3Field(null=True, blank=True)
    updated_at = UpdatedDateTime3Field()

    class Meta:
        managed = False
        db_table = "payments"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "idempotency_key"), name="uq_pay_idem"
            ),
            models.CheckConstraint(
                condition=Q(amount_paise__gt=0) & Q(amount_paise__lte=10_000_000),
                name="chk_pay_amount",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(status="successful")
                    | (Q(confirmed_by__isnull=False) & Q(resolved_at__isnull=False))
                ),
                name="chk_pay_success",
            ),
        ]
        indexes = [
            models.Index(fields=("user", "initiated_at"), name="idx_pay_user_time"),
            models.Index(fields=("status", "initiated_at"), name="idx_pay_unresolved"),
        ]

    def __str__(self):
        return f"{self.reference_code}: {self.status}"


class PaymentEvent(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20, null=True, blank=True)
    to_status = models.CharField(max_length=20)
    source = models.CharField(max_length=20, null=True, blank=True)
    detail = models.JSONField(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "payment_events"
        indexes = [
            models.Index(fields=("payment", "created_at"), name="idx_pevents_payment")
        ]
