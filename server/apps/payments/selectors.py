"""Read queries for saved payees."""

from django.db.models import Q

from apps.payments.models import Payee, Payment


def list_payees(user, *, search="", favorite=None):
    queryset = Payee.objects.filter(user=user).select_related("default_category")
    if search:
        queryset = queryset.filter(Q(name__icontains=search) | Q(upi_id__icontains=search))
    if favorite is not None:
        queryset = queryset.filter(is_favorite=favorite)
    return queryset.order_by("-is_favorite", "-last_used_at", "name", "pk")


def get_payee(user, public_id):
    return Payee.objects.filter(user=user, public_id=public_id).select_related(
        "default_category"
    ).first()


def list_payments(user, *, status_value=None):
    queryset = Payment.objects.filter(user=user).select_related("payee", "upi_app").order_by("-initiated_at", "-pk")
    if status_value:
        queryset = queryset.filter(status=status_value)
    return queryset


def get_payment(user, public_id):
    return Payment.objects.filter(user=user, public_id=public_id).select_related(
        "payee", "upi_app", "expense", "expense__category"
    ).first()
