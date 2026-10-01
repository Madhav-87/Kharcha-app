"""Security and business-operation audit records."""

from django.db import models

from apps.accounts.models import User
from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    UnsignedBigAutoField,
    UnsignedBigIntegerField,
)


class AuditLog(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=60)
    entity_type = models.CharField(max_length=40, null=True, blank=True)
    entity_id = UnsignedBigIntegerField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=("user", "created_at"), name="idx_audit_user_time")
        ]
