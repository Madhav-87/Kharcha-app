"""Serializers for notification inbox and FCM device endpoints."""

import re

from rest_framework import serializers

from apps.notifications.models import Notification, UserDevice


class NotificationSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ("public_id", "type", "severity", "title", "body", "deep_link", "data", "is_read", "read_at", "created_at")
        read_only_fields = fields

    def get_is_read(self, obj):
        return obj.read_at is not None


class NotificationListFilterSerializer(serializers.Serializer):
    unread_only = serializers.BooleanField(required=False, default=False)
    type = serializers.ChoiceField(choices=Notification.Type.choices, required=False)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)


class NotificationReadSerializer(serializers.Serializer):
    is_read = serializers.BooleanField(default=True)


class DeviceRegisterSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=512, trim_whitespace=True)
    platform = serializers.ChoiceField(choices=UserDevice.Platform.choices)
    device_label = serializers.CharField(max_length=120, required=False, allow_blank=True, trim_whitespace=True)
    app_version = serializers.CharField(max_length=30, required=False, allow_blank=True, trim_whitespace=True)

    def validate_fcm_token(self, value):
        if not value or not re.fullmatch(r"[\x21-\x7e]{1,512}", value):
            raise serializers.ValidationError("Provide a valid ASCII FCM registration token.")
        return value


class DeviceUnregisterSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=512, trim_whitespace=True)

    def validate_fcm_token(self, value):
        if not value or not re.fullmatch(r"[\x21-\x7e]{1,512}", value):
            raise serializers.ValidationError("Provide a valid ASCII FCM registration token.")
        return value


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ("platform", "device_label", "app_version", "is_active", "last_seen_at", "created_at")
        read_only_fields = fields
