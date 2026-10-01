"""Support issue and privacy request serializers."""

from rest_framework import serializers

from apps.support.models import DataRequest, IssueReport


class IssueReportCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=160, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    expense_public_id = serializers.UUIDField(required=False)
    payment_public_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if attrs.get("expense_public_id") and attrs.get("payment_public_id"):
            raise serializers.ValidationError(
                "Link an issue to either an expense or a payment, not both."
            )
        return attrs


class IssueReportSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    expense_public_id = serializers.UUIDField(source="expense.public_id", read_only=True, allow_null=True)
    payment_public_id = serializers.UUIDField(source="payment.public_id", read_only=True, allow_null=True)

    class Meta:
        model = IssueReport
        fields = (
            "public_id", "subject", "description", "status", "expense_public_id",
            "payment_public_id", "created_at", "resolved_at",
        )
        read_only_fields = fields


class DataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataRequest
        fields = ("type", "status", "file_url", "scheduled_for", "created_at", "completed_at")
        read_only_fields = fields


class PrivacySerializer(serializers.Serializer):
    account_status = serializers.CharField()
    export_requests = DataRequestSerializer(many=True)
    deletion_request = DataRequestSerializer(allow_null=True)


class DeleteAccountSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("Confirm that you want to schedule account deletion.")
        return value
