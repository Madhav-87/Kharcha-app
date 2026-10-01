"""Saved-payee API serializers."""

from rest_framework import serializers

from apps.payments.models import Payee, Payment, UpiApp
from apps.payments.validators import validate_upi_id


class PayeeSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    default_category_public_id = serializers.UUIDField(source="default_category.public_id", read_only=True)

    class Meta:
        model = Payee
        fields = (
            "public_id", "name", "upi_id", "default_category_public_id", "is_favorite",
            "use_count", "last_used_at", "created_at",
        )
        read_only_fields = ("use_count", "last_used_at", "created_at")


class PayeeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    upi_id = serializers.CharField(max_length=100, validators=[validate_upi_id])
    default_category_public_id = serializers.UUIDField(required=False, allow_null=True)
    is_favorite = serializers.BooleanField(required=False, default=False)


class PayeeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    upi_id = serializers.CharField(max_length=100, validators=[validate_upi_id], required=False)
    default_category_public_id = serializers.UUIDField(required=False, allow_null=True)
    is_favorite = serializers.BooleanField(required=False)


class PaymentInitiateSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1, max_value=10_000_000)
    category_public_id = serializers.UUIDField()
    payee_public_id = serializers.UUIDField(required=False)
    payee_name = serializers.CharField(max_length=120, required=False, trim_whitespace=True)
    payee_upi_id = serializers.CharField(max_length=100, required=False, validators=[validate_upi_id])
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    upi_app_code = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("payee_public_id") and not (attrs.get("payee_name") and attrs.get("payee_upi_id")):
            raise serializers.ValidationError({
                "payee_public_id": "Choose a saved payee or provide payee_name and payee_upi_id."
            })
        return attrs


class PaymentResolveReportSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("completed", "not_completed"))


class VerifiedPaymentCallbackSerializer(serializers.Serializer):
    reference_code = serializers.CharField(max_length=40)
    status = serializers.ChoiceField(choices=(Payment.Status.SUCCESSFUL, Payment.Status.FAILED))
    upi_txn_ref = serializers.CharField(max_length=80, required=False, allow_blank=True)
    failure_reason = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["status"] == Payment.Status.SUCCESSFUL and not attrs.get("upi_txn_ref", "").strip():
            raise serializers.ValidationError({"upi_txn_ref": "A verified success requires a UPI transaction reference."})
        return attrs


class PaymentEventSerializer(serializers.Serializer):
    from_status = serializers.CharField(allow_null=True)
    to_status = serializers.CharField()
    source = serializers.CharField(allow_null=True)
    detail = serializers.JSONField(allow_null=True)
    created_at = serializers.DateTimeField()


class PaymentSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    upi_app_code = serializers.CharField(source="upi_app.code", read_only=True, allow_null=True)
    category_public_id = serializers.UUIDField(source="expense.category.public_id", read_only=True)
    events = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "public_id", "reference_code", "status", "payee_name", "payee_upi_id", "category_public_id",
            "amount_paise", "currency", "note", "upi_app_code", "upi_txn_ref",
            "failure_reason", "confirmed_by", "initiated_at", "redirected_at", "resolved_at", "events",
        )
        read_only_fields = fields

    def get_events(self, obj):
        if not self.context.get("include_events", False):
            return []
        return PaymentEventSerializer(obj.events.order_by("created_at", "pk"), many=True).data


class UpiAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpiApp
        fields = ("code", "display_name", "android_package", "ios_scheme")
        read_only_fields = fields
