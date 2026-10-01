"""Reconcile stale UPI attempts without guessing their financial outcome."""

from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.payments.models import Payment
from apps.payments.services import _set_payment_status


@transaction.atomic
def reconcile_stale_payments(*, older_than_minutes=20, batch_size=500, now=None):
    """Move stale initiated/processing attempts to unknown for follow-up.

    No bank result is inferred: a successful/failed result must come from a
    signed provider callback or a later trusted reconciliation source.
    """
    now = now or timezone.now()
    cutoff = now - timedelta(minutes=older_than_minutes)
    stale = list(
        Payment.objects.select_for_update(skip_locked=True)
        .filter(status__in=(Payment.Status.INITIATED, Payment.Status.PROCESSING), initiated_at__lte=cutoff)
        .filter(Q(redirected_at__isnull=True) | Q(redirected_at__lte=cutoff))
        .order_by("initiated_at", "pk")[:batch_size]
    )
    for payment in stale:
        _set_payment_status(
            payment,
            Payment.Status.UNKNOWN,
            confirmed_by=Payment.ConfirmedBy.RECONCILIATION,
            failure_reason="No verified payment result was received before reconciliation.",
        )
    return len(stale)
