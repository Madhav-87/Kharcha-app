from django.urls import path

from apps.payments.views import (
    PaymentDetailView,
    PaymentInitiateView,
    PaymentListView,
    PaymentRedirectedView,
    PaymentReportView,
    UpiAppListView,
    VerifiedUpiCallbackView,
)

urlpatterns = [
    path("callbacks/upi/", VerifiedUpiCallbackView.as_view(), name="upi-payment-callback"),
    path("upi-apps/", UpiAppListView.as_view(), name="upi-app-list"),
    path("initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("", PaymentListView.as_view(), name="payment-list"),
    path("<uuid:public_id>/redirected/", PaymentRedirectedView.as_view(), name="payment-redirected"),
    path("<uuid:public_id>/report/", PaymentReportView.as_view(), name="payment-report"),
    path("<uuid:public_id>/", PaymentDetailView.as_view(), name="payment-detail"),
]
