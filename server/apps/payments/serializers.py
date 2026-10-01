"""Saved-payee API serializers."""

from rest_framework import serializers

from apps.payments.models import Payee
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
