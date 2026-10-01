from django.urls import path

from apps.payments.payee_views import PayeeDetailView, PayeeListCreateView

urlpatterns = [
    path("", PayeeListCreateView.as_view(), name="payee-list-create"),
    path("<uuid:public_id>/", PayeeDetailView.as_view(), name="payee-detail"),
]
