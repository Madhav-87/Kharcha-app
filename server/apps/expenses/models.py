"""Manual and payment-linked expense records."""

from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.categories.models import Category
from apps.payments.models import Payee, Payment
from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    PublicIdField,
    UnsignedBigAutoField,
    UnsignedBigIntegerField,
    UpdatedDateTime3Field,
)


class Expense(models.Model):
    class Method(models.TextChoices):
        UPI = "upi", "UPI"
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        NETBANKING = "netbanking", "Net banking"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        UPI_PAYMENT = "upi_payment", "UPI payment"

    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="expenses")
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expense",
    )
    payee = models.ForeignKey(
        Payee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    title = models.CharField(max_length=160)
    amount_paise = UnsignedBigIntegerField()
    note = models.CharField(max_length=500, null=True, blank=True)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.UPI)
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=11, choices=Source.choices, default=Source.MANUAL)
    expense_at = DatabaseNowDateTime3Field()
    deleted_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()
    updated_at = UpdatedDateTime3Field()

    class Meta:
        managed = False
        db_table = "expenses"
        constraints = [
            models.CheckConstraint(condition=Q(amount_paise__gt=0), name="chk_exp_amount")
        ]
        indexes = [
            models.Index(fields=("user", "deleted_at", "expense_at"), name="idx_exp_user_time"),
            models.Index(fields=("user", "category", "status", "expense_at"), name="idx_exp_user_cat"),
            models.Index(fields=("user", "status", "expense_at"), name="idx_exp_user_status"),
        ]

    def __str__(self):
        return self.title
