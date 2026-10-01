"""Support issues and user privacy/data-management requests."""

from django.db import models

from apps.accounts.models import User
from apps.expenses.models import Expense
from apps.payments.models import Payment
from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    PublicIdField,
    UnsignedBigAutoField,
)


class IssueReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="issue_reports")
    expense = models.ForeignKey(
        Expense,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issue_reports",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issue_reports",
    )
    subject = models.CharField(max_length=160)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = DatabaseNowDateTime3Field()
    resolved_at = DateTime3Field(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "issue_reports"
        indexes = [models.Index(fields=("user", "created_at"), name="idx_issue_user")]

    def __str__(self):
        return self.subject


class DataRequest(models.Model):
    class RequestType(models.TextChoices):
        EXPORT = "export", "Export"
        DELETE_ACCOUNT = "delete_account", "Delete account"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="data_requests")
    type = models.CharField(max_length=14, choices=RequestType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    file_url = models.CharField(max_length=500, null=True, blank=True)
    scheduled_for = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()
    completed_at = DateTime3Field(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "data_requests"
        indexes = [models.Index(fields=("user", "type", "status"), name="idx_dreq_user")]
