from django.urls import path

from apps.notifications.views import (
    DeviceListRegisterView,
    DeviceUnregisterView,
    NotificationDetailView,
    NotificationListView,
    NotificationReadAllView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    path("devices/", DeviceListRegisterView.as_view(), name="device-list-register"),
    path("devices/unregister/", DeviceUnregisterView.as_view(), name="device-unregister"),
    path("<uuid:public_id>/", NotificationDetailView.as_view(), name="notification-detail"),
]
