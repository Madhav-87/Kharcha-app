"""Background privacy export generation."""

import json
import os
import tempfile
from pathlib import Path

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core import signing
from django.utils import timezone

from apps.accounts.services import record_audit
from apps.support.constants import EXPORT_TOKEN_SALT
from apps.support.models import DataRequest
from apps.support.services import build_user_export


@shared_task(bind=True, name="support.build_data_export", max_retries=3)
def build_data_export_task(self, request_id):
    data_request = DataRequest.objects.filter(
        pk=request_id, type=DataRequest.RequestType.EXPORT
    ).select_related("user").first()
    if data_request is None or data_request.status in (
        DataRequest.Status.CANCELLED, DataRequest.Status.COMPLETED
    ):
        return

    DataRequest.objects.filter(pk=data_request.pk).update(status=DataRequest.Status.PROCESSING)
    export_root = Path(settings.PRIVATE_EXPORT_ROOT)
    export_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = export_root / f"request-{data_request.pk}.json"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=export_root, delete=False
        ) as output:
            temp_name = output.name
            json.dump(build_user_export(data_request.user), output, ensure_ascii=False, indent=2, default=str)
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, target)
        token = signing.dumps(
            {"request_id": data_request.pk, "user": str(data_request.user.public_id)},
            salt=EXPORT_TOKEN_SALT,
        )
        DataRequest.objects.filter(pk=data_request.pk).update(
            status=DataRequest.Status.COMPLETED,
            completed_at=timezone.now(),
            file_url=f"/api/v1/settings/export-data/{token}/download/",
        )
        record_audit(
            data_request.user,
            "data_export_completed",
            entity_type="data_request",
            entity_id=data_request.pk,
        )
    except Exception as exc:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
        DataRequest.objects.filter(pk=data_request.pk).update(status=DataRequest.Status.REQUESTED)
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            raise exc
