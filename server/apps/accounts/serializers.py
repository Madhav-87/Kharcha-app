"""Request validation and public response serializers for account APIs."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.validators import validate_indian_phone


class PasswordRulesMixin:
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class RegisterSerializer(PasswordRulesMixin, serializers.Serializer):
    full_name = serializers.CharField(max_length=120)
    display_name = serializers.CharField(max_length=60, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=255)
    phone = serializers.CharField(
        max_length=13, required=False, allow_blank=True, validators=[validate_indian_phone]
    )
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=10)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    college_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    monthly_budget_paise = serializers.IntegerField(required=False, min_value=1)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_phone(self, value):
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return value or None

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            validate_password(
                attrs["password"],
                user=User(
                    email=attrs["email"],
                    full_name=attrs["full_name"],
                    display_name=attrs.get("display_name"),
                ),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    device_label = serializers.CharField(max_length=120, required=False, allow_blank=True)


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True, trim_whitespace=False)
    device_label = serializers.CharField(max_length=120, required=False, allow_blank=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(write_only=True, trim_whitespace=False)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def validate_email(self, value):
        return value.strip().lower()


class ResetPasswordSerializer(PasswordRulesMixin, serializers.Serializer):
    token = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=10)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class ChangePasswordSerializer(PasswordRulesMixin, serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=10)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context.get("request").user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class ProfileSerializer(serializers.Serializer):
    public_id = serializers.CharField(read_only=True)
    full_name = serializers.CharField(max_length=120, required=False)
    display_name = serializers.CharField(max_length=60, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(
        max_length=13,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_indian_phone],
    )
    college_name = serializers.CharField(max_length=160, required=False, allow_blank=True, allow_null=True)
    avatar_url = serializers.CharField(max_length=500, read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_phone(self, value):
        value = value or None
        request = self.context.get("request")
        if value and request and User.objects.filter(phone=value).exclude(pk=request.user.pk).exists():
            raise serializers.ValidationError("That phone number is already in use.")
        return value


class SettingsSerializer(serializers.Serializer):
    monthly_budget_paise = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    currency = serializers.ChoiceField(choices=("INR",), required=False)
    budget_alert_threshold = serializers.IntegerField(required=False, min_value=1, max_value=100)
    push_enabled = serializers.BooleanField(required=False)
    notify_budget_alerts = serializers.BooleanField(required=False)
    notify_payment_updates = serializers.BooleanField(required=False)
    notify_system = serializers.BooleanField(required=False)
    default_category_public_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    preferred_upi_app_code = serializers.CharField(max_length=30, required=False, allow_blank=True, write_only=True)

    def to_representation(self, instance):
        data = {
            "monthly_budget_paise": instance.monthly_budget_paise,
            "currency": instance.currency,
            "budget_alert_threshold": instance.budget_alert_threshold,
            "push_enabled": instance.push_enabled,
            "notify_budget_alerts": instance.notify_budget_alerts,
            "notify_payment_updates": instance.notify_payment_updates,
            "notify_system": instance.notify_system,
            "default_category_public_id": str(instance.default_category.public_id)
            if instance.default_category_id else None,
            "preferred_upi_app_code": instance.preferred_upi_app.code
            if instance.preferred_upi_app_id else None,
        }
        return data


class OnboardingPatchSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=60, required=False, allow_blank=True)
    monthly_budget_paise = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    category_public_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True, max_length=50
    )
    onboarding_step = serializers.IntegerField(required=False, min_value=1, max_value=3)


class SessionSerializer(serializers.Serializer):
    public_id = serializers.CharField()
    device_label = serializers.CharField(allow_null=True)
    user_agent = serializers.CharField(allow_null=True)
    ip_address = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    last_active_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    revoked_at = serializers.DateTimeField(allow_null=True)
    is_current = serializers.BooleanField()
