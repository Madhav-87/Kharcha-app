"""Payment initiation, status, callback, and reconciliation-facing APIs."""

from django.core.paginator import EmptyPage, Paginator
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.payments import selectors, services
from apps.payments.callbacks import verify_callback_signature
from apps.payments.models import Payment, UpiApp
from apps.payments.serializers import (
    PaymentInitiateSerializer,
    PaymentResolveReportSerializer,
    PaymentSerializer,
    VerifiedPaymentCallbackSerializer,
    UpiAppSerializer,
)


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


class PaymentListView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        status_value = request.query_params.get("status")
        if status_value and status_value not in Payment.Status.values:
            raise ValidationError({"status": "Choose a valid payment status."})
        try:
            page_number = int(request.query_params.get("page", "1"))
            page_size = int(request.query_params.get("page_size", "20"))
        except ValueError as exc:
            raise ValidationError({"page": "Page and page_size must be integers."}) from exc
        if page_number < 1 or not 1 <= page_size <= 100:
            raise ValidationError({"page": "Page must be positive and page_size must be between 1 and 100."})
        paginator = Paginator(selectors.list_payments(request.user, status_value=status_value), page_size)
        try:
            page = paginator.page(page_number)
        except EmptyPage as exc:
            raise ValidationError({"page": "No payments exist on this page."}) from exc
        return Response(_success({
            "results": PaymentSerializer(page.object_list, many=True).data,
            "pagination": {
                "page": page.number, "page_size": page_size, "total": paginator.count,
                "total_pages": paginator.num_pages, "has_next": page.has_next(),
                "has_previous": page.has_previous(),
            },
        }))


class UpiAppListView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        apps = UpiApp.objects.filter(is_active=True).order_by("sort_order", "display_name")
        return Response(_success(UpiAppSerializer(apps, many=True).data))


class PaymentInitiateView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.initiate_payment(
            request.user, serializer.validated_data, request.headers.get("Idempotency-Key", "")
        )
        payment_data = PaymentSerializer(result["payment"], context={"include_events": True}).data
        return Response(_success({
            "payment": payment_data,
            "upi_uri": result["upi_uri"],
            "idempotent_replay": result["idempotent_replay"],
        }, "Payment intent created."), status=status.HTTP_200_OK if result["idempotent_replay"] else status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, public_id):
        payment = selectors.get_payment(request.user, public_id)
        if payment is None:
            raise NotFound("Payment was not found.")
        return Response(_success(PaymentSerializer(payment, context={"include_events": True}).data))


class PaymentRedirectedView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, public_id):
        payment = services.mark_redirected(request.user, public_id)
        return Response(_success(PaymentSerializer(payment, context={"include_events": True}).data, "Payment handoff recorded."))


class PaymentReportView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, public_id):
        serializer = PaymentResolveReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = services.report_user_outcome(
            request.user, public_id, serializer.validated_data["outcome"]
        )
        return Response(_success(PaymentSerializer(payment, context={"include_events": True}).data, "Payment outcome recorded for reconciliation."))


class VerifiedUpiCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        verify_callback_signature(request.body, request.headers.get("X-UPI-Signature", ""))
        serializer = VerifiedPaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = Payment.objects.filter(reference_code=serializer.validated_data["reference_code"]).first()
        if payment is None:
            raise NotFound("Payment reference was not found.")
        payment = services.apply_verified_result(
            payment,
            serializer.validated_data["status"],
            upi_txn_ref=serializer.validated_data.get("upi_txn_ref", ""),
            failure_reason=serializer.validated_data.get("failure_reason", ""),
        )
        return Response(_success(PaymentSerializer(payment).data, "Verified payment result applied."))
