"""Read queries for saved payees."""

from django.db.models import Q

from apps.payments.models import Payee


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
