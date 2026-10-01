"""Celery tasks for scheduled payment reconciliation."""

from celery import shared_task

from apps.payments.reconciliation import reconcile_stale_payments


@shared_task(name="payments.reconcile_stale_payments")
def reconcile_stale_payment_task(older_than_minutes=20, batch_size=500):
    return reconcile_stale_payments(
        older_than_minutes=older_than_minutes,
        batch_size=batch_size,
    )
