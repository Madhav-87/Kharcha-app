"""In-app notification inbox and FCM device-token endpoints."""

from django.core.paginator import EmptyPage, Paginator
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.notifications import selectors, services
from apps.notifications.serializers import (
    DeviceRegisterSerializer,
    DeviceSerializer,
    DeviceUnregisterSerializer,
    NotificationListFilterSerializer,
    NotificationReadSerializer,
    NotificationSerializer,
)


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


class NotificationListView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        serializer = NotificationListFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        queryset = selectors.list_notifications(
            request.user,
            unread_only=filters["unread_only"],
            notification_type=filters.get("type"),
        )
        paginator = Paginator(queryset, filters["page_size"])
        try:
            page = paginator.page(filters["page"])
        except EmptyPage as exc:
            raise ValidationError({"page": "No notifications exist on this page."}) from exc
        return Response(_success({
            "results": NotificationSerializer(page.object_list, many=True).data,
            "unread_count": selectors.unread_count(request.user),
            "pagination": {
                "page": page.number,
                "page_size": filters["page_size"],
                "total": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
            },
        }))


class NotificationReadAllView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        count = services.mark_all_notifications_read(request.user)
        return Response(_success({"updated": count}, "Notifications marked as read."))


class NotificationDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def patch(self, request, public_id):
        serializer = NotificationReadSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        notification = services.mark_notification_read(
            request.user, public_id, is_read=serializer.validated_data.get("is_read", True)
        )
        return Response(_success(NotificationSerializer(notification).data, "Notification updated."))


class DeviceListRegisterView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        devices = selectors.list_devices(request.user)
        return Response(_success(DeviceSerializer(devices, many=True).data))

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = services.register_device(request.user, serializer.validated_data)
        return Response(
            _success(DeviceSerializer(device).data, "Push device registered."),
            status=status.HTTP_200_OK,
        )


class DeviceUnregisterView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        serializer = DeviceUnregisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        count = services.unregister_device(request.user, serializer.validated_data["fcm_token"])
        return Response(_success({"unregistered": bool(count)}, "Push device unregistered."))
