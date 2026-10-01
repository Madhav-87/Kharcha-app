"""Payment initiation, idempotency, and state-transition workflows."""

import secrets

from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.categories.models import Category
from apps.expenses.models import Expense
from apps.payments.models import Payee, Payment, UpiApp
from apps.budgets.alerts import evaluate_budget_alerts


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = "This idempotency key was already used for a different payment request."
    default_code = "IDEMPOTENCY_CONFLICT"


class PaymentStateConflict(APIException):
    status_code = 409
    default_detail = "The payment is already in a state that cannot accept this update."
    default_code = "PAYMENT_STATE_CONFLICT"


def _find_category(user, public_id):
    category = Category.objects.filter(public_id=public_id, archived_at__isnull=True).filter(
        Q(user__isnull=True) | Q(user=user)
    ).first()
    if category is None:
        raise ValidationError({"category_public_id": "Choose an available category."})
    return category


def _resolve_recipient(user, values):
    payee = None
    if values.get("payee_public_id"):
        payee = Payee.objects.filter(user=user, public_id=values["payee_public_id"]).first()
        if payee is None:
            raise ValidationError({"payee_public_id": "Choose one of your saved payees."})
        return payee.name, payee.upi_id, payee
    return values["payee_name"], values["payee_upi_id"], None


def _request_matches(payment, *, name, upi_id, amount, note, category, upi_app):
    expense = Expense.objects.filter(payment=payment).first()
    return (
        payment.payee_name == name
        and payment.payee_upi_id == upi_id
        and payment.amount_paise == amount
        and payment.note == note
        and payment.upi_app_id == (upi_app.pk if upi_app else None)
        and expense is not None
        and expense.category_id == category.pk
    )


def _intent_response(payment, *, reused=False):
    from apps.payments.upi import build_upi_intent

    return {"payment": payment, "upi_uri": build_upi_intent(payment), "idempotent_replay": reused}


@transaction.atomic
def initiate_payment(user, values, idempotency_key):
    if not idempotency_key or not 8 <= len(idempotency_key) <= 80:
        raise ValidationError({"Idempotency-Key": "Provide an 8-80 character idempotency key."})
    category = _find_category(user, values["category_public_id"])
    name, upi_id, payee = _resolve_recipient(user, values)
    upi_app = None
    app_code = values.get("upi_app_code", "").strip()
    if app_code:
        upi_app = UpiApp.objects.filter(code=app_code, is_active=True).first()
        if upi_app is None:
            raise ValidationError({"upi_app_code": "Choose an active UPI app."})
    amount = values["amount_paise"]
    note = values.get("note") or None

    existing = Payment.objects.filter(user=user, idempotency_key=idempotency_key).first()
    if existing:
        if not _request_matches(existing, name=name, upi_id=upi_id, amount=amount, note=note, category=category, upi_app=upi_app):
            raise IdempotencyConflict()
        return _intent_response(existing, reused=True)

    # Savepoint allows recovery from concurrent use of the same idempotency key.
    created = False
    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                user=user,
                payee=payee,
                payee_name=name,
                payee_upi_id=upi_id,
                amount_paise=amount,
                currency="INR",
                note=note,
                upi_app=upi_app,
                status=Payment.Status.INITIATED,
                reference_code=f"SF{secrets.token_hex(8).upper()}",
                idempotency_key=idempotency_key,
            )
            created = True
    except IntegrityError:
        payment = Payment.objects.select_for_update().filter(
            user=user, idempotency_key=idempotency_key
        ).first()
        if payment is None:
            raise
    if not created:
        if not _request_matches(payment, name=name, upi_id=upi_id, amount=amount, note=note, category=category, upi_app=upi_app):
            raise IdempotencyConflict()
        return _intent_response(payment, reused=True)

    # Payment insert triggers append the initial payment_event row in MySQL.
    Expense.objects.create(
        user=user,
        category=category,
        payment=payment,
        payee=payee,
        title=name,
        amount_paise=amount,
        note=note,
        method=Expense.Method.UPI,
        status=Expense.Status.PENDING,
        source=Expense.Source.UPI_PAYMENT,
    )
    if payee:
        Payee.objects.filter(pk=payee.pk).update(use_count=F("use_count") + 1, last_used_at=timezone.now())
    return _intent_response(payment)


def require_payment(user, public_id, *, lock=False):
    queryset = Payment.objects.filter(user=user, public_id=public_id)
    if lock:
        queryset = queryset.select_for_update()
    payment = queryset.select_related("payee", "upi_app").first()
    if payment is None:
        raise NotFound("Payment was not found.")
    return payment


def _set_payment_status(payment, new_status, *, confirmed_by=None, upi_txn_ref=None, failure_reason=None):
    current = payment.status
    if current == new_status:
        return payment
    allowed = {
        Payment.Status.INITIATED: {Payment.Status.PROCESSING, Payment.Status.UNKNOWN, Payment.Status.CANCELLED, Payment.Status.SUCCESSFUL, Payment.Status.FAILED},
        Payment.Status.PROCESSING: {Payment.Status.UNKNOWN, Payment.Status.CANCELLED, Payment.Status.SUCCESSFUL, Payment.Status.FAILED},
        Payment.Status.UNKNOWN: {Payment.Status.SUCCESSFUL, Payment.Status.FAILED, Payment.Status.CANCELLED},
        Payment.Status.SUCCESSFUL: set(),
        Payment.Status.FAILED: set(),
        Payment.Status.CANCELLED: set(),
    }
    if new_status not in allowed.get(current, set()):
        raise PaymentStateConflict()
    now = timezone.now()
    payment.status = new_status
    payment.confirmed_by = confirmed_by
    if new_status in (Payment.Status.SUCCESSFUL, Payment.Status.FAILED, Payment.Status.CANCELLED):
        payment.resolved_at = now
    if upi_txn_ref:
        payment.upi_txn_ref = upi_txn_ref
    payment.failure_reason = failure_reason or None
    payment.save(update_fields=("status", "confirmed_by", "resolved_at", "upi_txn_ref", "failure_reason", "updated_at"))
    # MySQL status trigger synchronizes the associated expense status and appends an event.
    if new_status == Payment.Status.SUCCESSFUL:
        expense = Expense.objects.filter(payment=payment).first()
        if expense:
            evaluate_budget_alerts(
                payment.user,
                expense.expense_at.date().replace(day=1),
                category_ids=[expense.category_id],
            )
    return payment


@transaction.atomic
def mark_redirected(user, public_id):
    payment = require_payment(user, public_id, lock=True)
    if payment.status == Payment.Status.PROCESSING:
        return payment
    if payment.status != Payment.Status.INITIATED:
        raise PaymentStateConflict()
    payment.redirected_at = timezone.now()
    payment.save(update_fields=("redirected_at", "updated_at"))
    return _set_payment_status(
        payment, Payment.Status.PROCESSING, confirmed_by=Payment.ConfirmedBy.USER_MANUAL
    )


@transaction.atomic
def report_user_outcome(user, public_id, outcome):
    payment = require_payment(user, public_id, lock=True)
    if outcome == "completed":
        return _set_payment_status(
            payment, Payment.Status.UNKNOWN,
            confirmed_by=Payment.ConfirmedBy.USER_MANUAL,
            failure_reason=None,
        )
    return _set_payment_status(
        payment, Payment.Status.CANCELLED,
        confirmed_by=Payment.ConfirmedBy.USER_MANUAL,
        failure_reason="User reported payment not completed.",
    )


@transaction.atomic
def apply_verified_result(payment, status_value, *, upi_txn_ref="", failure_reason="", confirmed_by=Payment.ConfirmedBy.UPI_CALLBACK):
    locked = Payment.objects.select_for_update().get(pk=payment.pk)
    return _set_payment_status(
        locked,
        status_value,
        confirmed_by=confirmed_by,
        upi_txn_ref=upi_txn_ref,
        failure_reason=failure_reason,
    )
