"""Support and user privacy endpoints."""

from pathlib import Path

from django.conf import settings
from django.core import signing
from django.http import FileResponse
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.support import services
from apps.support.constants import EXPORT_TOKEN_SALT
from apps.support.models import DataRequest
from apps.support.serializers import (
    DataRequestSerializer,
    DeleteAccountSerializer,
    IssueReportCreateSerializer,
    IssueReportSerializer,
    PrivacySerializer,
)


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


def _request_ip(request):
    return request.META.get("REMOTE_ADDR") or None


class IssueListCreateView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        try:
            page = int(request.query_params.get("page", "1"))
            page_size = int(request.query_params.get("page_size", "20"))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"page": "Page and page_size must be positive integers."}) from exc
        if page < 1 or page_size < 1:
            raise ValidationError({"page": "Page and page_size must be positive integers."})
        page_size = min(100, page_size)
        queryset = services.list_issues(request.user)
        total = queryset.count()
        results = queryset[(page - 1) * page_size:page * page_size]
        return Response(
            _success(
                {
                    "results": IssueReportSerializer(results, many=True).data,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size,
                    },
                }
            )
        )

    def post(self, request):
        serializer = IssueReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue = services.create_issue(
            request.user, serializer.validated_data, ip_address=_request_ip(request)
        )
        issue = services.get_issue(request.user, issue.public_id)
        return Response(
            _success(IssueReportSerializer(issue).data, "Support issue submitted."),
            status=status.HTTP_201_CREATED,
        )


class IssueDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, public_id):
        issue = services.get_issue(request.user, public_id)
        return Response(_success(IssueReportSerializer(issue).data))


class PrivacyView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        return Response(_success(PrivacySerializer(services.privacy_status(request.user)).data))


class ExportDataView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        data_request = services.request_data_export(request.user, ip_address=_request_ip(request))
        return Response(
            _success(DataRequestSerializer(data_request).data, "Data export requested."),
            status=status.HTTP_202_ACCEPTED,
        )


class ExportDownloadView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, token):
        try:
            payload = signing.loads(token, salt=EXPORT_TOKEN_SALT)
        except signing.BadSignature as exc:
            raise NotFound("Export link is invalid or expired.") from exc
        if not isinstance(payload, dict):
            raise NotFound("Export link is invalid.")
        data_request = DataRequest.objects.filter(
            pk=payload.get("request_id"),
            user=request.user,
            type=DataRequest.RequestType.EXPORT,
            status=DataRequest.Status.COMPLETED,
        ).first()
        if data_request is None:
            raise NotFound("Export was not found.")
        expected_user = str(request.user.public_id)
        if payload.get("user") != expected_user:
            raise NotFound("Export was not found.")
        path = Path(settings.PRIVATE_EXPORT_ROOT) / f"request-{data_request.pk}.json"
        if not path.is_file():
            raise NotFound("Export file is no longer available.")
        return FileResponse(
            path.open("rb"),
            as_attachment=True,
            filename=f"student-finance-export-{data_request.created_at:%Y%m%d}.json",
            content_type="application/json",
        )


class DeleteAccountView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_request, created = services.request_account_deletion(
            request.user, ip_address=_request_ip(request)
        )
        message = (
            "Account deletion scheduled."
            if created
            else "An account deletion request is already active."
        )
        return Response(
            _success(DataRequestSerializer(data_request).data, message),
            status=status.HTTP_202_ACCEPTED,
        )

    def delete(self, request):
        data_request = services.cancel_account_deletion(request.user, ip_address=_request_ip(request))
        return Response(
            _success(DataRequestSerializer(data_request).data, "Account deletion request cancelled.")
        )
