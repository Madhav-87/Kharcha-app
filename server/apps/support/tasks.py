"""Background privacy export generation."""

import json
import os
import tempfile
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import record_audit
from apps.support.constants import EXPORT_TOKEN_SALT
from apps.support.models import DataRequest
from apps.support.services import build_user_export, process_due_account_deletion


@shared_task(bind=True, name="support.build_data_export", max_retries=3)
def build_data_export_task(self, request_id):
    temp_name = None
    target_path = None
    try:
        user_id = DataRequest.objects.filter(
            pk=request_id, type=DataRequest.RequestType.EXPORT
        ).values_list("user_id", flat=True).first()
        if user_id is None:
            return
        with transaction.atomic():
            user = User.objects.select_for_update().filter(pk=user_id).first()
            if user is None:
                return
            data_request = DataRequest.objects.select_for_update().filter(
                pk=request_id,
                user=user,
                type=DataRequest.RequestType.EXPORT,
            ).first()
            if data_request is None or data_request.status in (
                DataRequest.Status.CANCELLED, DataRequest.Status.COMPLETED
            ):
                return

            data_request.status = DataRequest.Status.PROCESSING
            data_request.save(update_fields=("status",))
            export_root = Path(settings.PRIVATE_EXPORT_ROOT)
            export_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(export_root, 0o700)
            target_path = export_root / f"request-{data_request.pk}.json"
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=export_root, delete=False
            ) as output:
                temp_name = output.name
                json.dump(
                    build_user_export(user),
                    output,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, target_path)
            temp_name = None
            token = signing.dumps(
                {"request_id": data_request.pk, "user": str(user.public_id)},
                salt=EXPORT_TOKEN_SALT,
            )
            data_request.status = DataRequest.Status.COMPLETED
            data_request.completed_at = timezone.now()
            data_request.file_url = f"/api/v1/settings/export-data/{token}/download/"
            data_request.save(update_fields=("status", "completed_at", "file_url"))
            record_audit(
                user,
                "data_export_completed",
                entity_type="data_request",
                entity_id=data_request.pk,
            )
    except Exception as exc:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
        if target_path and target_path.exists():
            target_path.unlink(missing_ok=True)
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            raise exc


@shared_task(name="support.expire_data_exports")
def expire_data_exports(retention_days=7, batch_size=1000):
    cutoff = timezone.now() - timedelta(days=retention_days)
    expired = list(
        DataRequest.objects.filter(
            type=DataRequest.RequestType.EXPORT,
            status=DataRequest.Status.COMPLETED,
            created_at__lt=cutoff,
            file_url__isnull=False,
        ).order_by("created_at", "pk")[:batch_size]
    )
    export_root = Path(settings.PRIVATE_EXPORT_ROOT)
    for data_request in expired:
        file_path = export_root / f"request-{data_request.pk}.json"
        file_path.unlink(missing_ok=True)
        DataRequest.objects.filter(pk=data_request.pk).update(file_url=None)
    return len(expired)


@shared_task(name="support.process_due_account_deletions")
def process_due_account_deletions_task(batch_size=100):
    request_ids = list(
        DataRequest.objects.filter(
            type=DataRequest.RequestType.DELETE_ACCOUNT,
            status=DataRequest.Status.REQUESTED,
            scheduled_for__lte=timezone.now(),
        ).order_by("scheduled_for", "pk").values_list("pk", flat=True)[:batch_size]
    )
    results = {"deleted": 0, "deferred": 0, "skipped": 0}
    for request_id in request_ids:
        result = process_due_account_deletion(request_id)
        results[result] += 1
    return results
