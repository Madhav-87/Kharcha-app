"""Support workflows and privacy request handling."""

from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.models import User
from apps.accounts.services import record_audit
from apps.audit.models import AuditLog
from apps.expenses.models import Expense
from apps.payments.models import Payment
from apps.support.models import DataRequest, IssueReport

DELETION_GRACE_DAYS = 30


@transaction.atomic
def create_issue(user, values, *, ip_address=None):
    locked_user = User.objects.select_for_update().filter(pk=user.pk).first()
    if locked_user is None:
        raise NotFound("Account was not found.")
    user = locked_user
    data = dict(values)
    expense_public_id = data.pop("expense_public_id", None)
    payment_public_id = data.pop("payment_public_id", None)
    expense = None
    payment = None
    if expense_public_id:
        expense = Expense.objects.filter(user=user, public_id=expense_public_id).first()
        if expense is None:
            raise ValidationError({"expense_public_id": "This expense is unavailable."})
    if payment_public_id:
        payment = Payment.objects.filter(user=user, public_id=payment_public_id).first()
        if payment is None:
            raise ValidationError({"payment_public_id": "This payment is unavailable."})

    issue = IssueReport.objects.create(
        user=user, expense=expense, payment=payment, **data
    )
    record_audit(
        user,
        "support_issue_created",
        entity_type="issue_report",
        entity_id=issue.pk,
        ip_address=ip_address,
        metadata={"linked_to": "payment" if payment else "expense" if expense else "account"},
    )
    return issue


def list_issues(user):
    return (
        IssueReport.objects.filter(user=user)
        .select_related("expense", "payment")
        .order_by("-created_at", "-pk")
    )


def get_issue(user, public_id):
    issue = (
        IssueReport.objects.filter(user=user, public_id=public_id)
        .select_related("expense", "payment")
        .first()
    )
    if issue is None:
        raise NotFound("Issue report was not found.")
    return issue


def privacy_status(user):
    exports = DataRequest.objects.filter(
        user=user, type=DataRequest.RequestType.EXPORT
    ).order_by("-created_at", "-pk")[:20]
    deletion = DataRequest.objects.filter(
        user=user,
        type=DataRequest.RequestType.DELETE_ACCOUNT,
        status__in=(DataRequest.Status.REQUESTED, DataRequest.Status.PROCESSING),
    ).order_by("-created_at", "-pk").first()
    return {
        "account_status": user.status,
        "export_requests": exports,
        "deletion_request": deletion,
    }


@transaction.atomic
def request_data_export(user, *, ip_address=None):
    locked_user = User.objects.select_for_update().filter(pk=user.pk).first()
    if locked_user is None:
        raise NotFound("Account was not found.")
    user = locked_user
    request = DataRequest.objects.create(user=user, type=DataRequest.RequestType.EXPORT)
    record_audit(
        user, "data_export_requested", entity_type="data_request", entity_id=request.pk,
        ip_address=ip_address,
    )
    from apps.support.tasks import build_data_export_task

    transaction.on_commit(lambda: build_data_export_task.delay(request.pk), robust=True)
    return request


@transaction.atomic
def request_account_deletion(user, *, ip_address=None):
    locked_user = User.objects.select_for_update().filter(pk=user.pk).first()
    if locked_user is None:
        raise NotFound("Account was not found.")
    user = locked_user
    current = DataRequest.objects.select_for_update().filter(
        user=user,
        type=DataRequest.RequestType.DELETE_ACCOUNT,
        status__in=(DataRequest.Status.REQUESTED, DataRequest.Status.PROCESSING),
    ).order_by("-created_at", "-pk").first()
    if current:
        return current, False
    now = timezone.now()
    request = DataRequest.objects.create(
        user=user,
        type=DataRequest.RequestType.DELETE_ACCOUNT,
        scheduled_for=now + timedelta(days=DELETION_GRACE_DAYS),
    )
    record_audit(
        user, "account_deletion_requested", entity_type="data_request", entity_id=request.pk,
        ip_address=ip_address,
        metadata={"grace_period_days": DELETION_GRACE_DAYS},
    )
    return request, True


@transaction.atomic
def cancel_account_deletion(user, *, ip_address=None):
    request = DataRequest.objects.select_for_update().filter(
        user=user,
        type=DataRequest.RequestType.DELETE_ACCOUNT,
        status=DataRequest.Status.REQUESTED,
    ).order_by("-created_at", "-pk").first()
    if request is None:
        raise NotFound("An active account deletion request was not found.")
    request.status = DataRequest.Status.CANCELLED
    request.save(update_fields=("status",))
    record_audit(
        user, "account_deletion_cancelled", entity_type="data_request", entity_id=request.pk,
        ip_address=ip_address,
    )
    return request


def build_user_export(user):
    """Return a JSON-compatible export without credentials or device secrets."""
    from apps.accounts.models import AuthSession, TwoFactorMethod, UserSettings
    from apps.audit.models import AuditLog
    from apps.budgets.models import CategoryBudget, MonthlyBudget
    from apps.categories.models import Category, UserCategory
    from apps.notifications.models import Notification
    from apps.payments.models import Payee, PaymentEvent

    def iso(value):
        return value.isoformat() if value else None

    settings_obj = UserSettings.objects.filter(user=user).select_related(
        "default_category", "preferred_upi_app"
    ).first()
    expenses = Expense.objects.filter(user=user).select_related(
        "category", "payee", "payment"
    ).order_by("id")
    payments = Payment.objects.filter(user=user).select_related("payee", "upi_app").order_by("id")
    payees = Payee.objects.filter(user=user).select_related("default_category").order_by("id")
    categories = UserCategory.objects.filter(user=user).select_related("category").order_by("sort_order")
    issue_reports = IssueReport.objects.filter(user=user).select_related("expense", "payment").order_by("id")
    data_requests = DataRequest.objects.filter(user=user).order_by("id")
    notifications = Notification.objects.filter(user=user).order_by("id")
    sessions = AuthSession.objects.filter(user=user).order_by("id")
    audit_events = AuditLog.objects.filter(user=user).order_by("id")
    payment_events = PaymentEvent.objects.filter(payment__user=user).select_related(
        "payment"
    ).order_by("id")

    return {
        "exported_at": iso(timezone.now()),
        "profile": {
            "public_id": str(user.public_id), "full_name": user.full_name,
            "display_name": user.display_name, "email": user.email, "phone": user.phone,
            "college_name": user.college_name, "avatar_url": user.avatar_url,
            "email_verified_at": iso(user.email_verified_at),
            "phone_verified_at": iso(user.phone_verified_at), "created_at": iso(user.created_at),
            "college": ({"name": user.college.name, "city": user.college.city,
                         "state": user.college.state} if user.college_id else None),
        },
        "settings": ({
            "monthly_budget_paise": settings_obj.monthly_budget_paise,
            "currency": settings_obj.currency,
            "default_category_public_id": str(settings_obj.default_category.public_id)
            if settings_obj.default_category_id else None,
            "preferred_upi_app_code": settings_obj.preferred_upi_app.code
            if settings_obj.preferred_upi_app_id else None,
            "budget_alert_threshold": settings_obj.budget_alert_threshold,
            "push_enabled": settings_obj.push_enabled,
            "notify_budget_alerts": settings_obj.notify_budget_alerts,
            "notify_payment_updates": settings_obj.notify_payment_updates,
            "notify_system": settings_obj.notify_system,
            "onboarding_step": settings_obj.onboarding_step,
            "onboarding_completed_at": iso(settings_obj.onboarding_completed_at),
        } if settings_obj else None),
        "selected_categories": [
            {"public_id": str(row.category.public_id), "name": row.category.name,
             "color_override": row.color_override, "icon_override": row.icon_override,
             "sort_order": row.sort_order, "hidden": row.hidden}
            for row in categories
        ],
        "custom_categories": [
            {"public_id": str(row.public_id), "name": row.name, "slug": row.slug,
             "icon": row.icon, "emoji": row.emoji, "color": row.color,
             "is_default": row.is_default, "sort_order": row.sort_order,
             "archived_at": iso(row.archived_at), "created_at": iso(row.created_at)}
            for row in Category.objects.filter(user=user).order_by("id")
        ],
        "expenses": [
            {"public_id": str(row.public_id), "title": row.title,
             "amount_paise": row.amount_paise, "note": row.note,
             "category_public_id": str(row.category.public_id), "method": row.method,
             "status": row.status, "source": row.source,
             "payment_public_id": str(row.payment.public_id) if row.payment_id else None,
             "payee_name": row.payee.name if row.payee_id else None,
             "expense_at": iso(row.expense_at), "deleted_at": iso(row.deleted_at)}
            for row in expenses
        ],
        "payments": [
            {"public_id": str(row.public_id), "payee_name": row.payee_name,
             "payee_upi_id": row.payee_upi_id, "amount_paise": row.amount_paise,
             "currency": row.currency, "note": row.note, "status": row.status,
             "upi_app": row.upi_app.display_name if row.upi_app_id else None,
             "reference_code": row.reference_code, "upi_txn_ref": row.upi_txn_ref,
             "confirmed_by": row.confirmed_by, "failure_reason": row.failure_reason,
             "initiated_at": iso(row.initiated_at), "resolved_at": iso(row.resolved_at)}
            for row in payments
        ],
        "payment_events": [
            {"payment_public_id": str(row.payment.public_id),
             "from_status": row.from_status, "to_status": row.to_status,
             "source": row.source, "detail": row.detail, "created_at": iso(row.created_at)}
            for row in payment_events
        ],
        "saved_payees": [
            {"public_id": str(row.public_id), "name": row.name, "upi_id": row.upi_id,
             "default_category_public_id": str(row.default_category.public_id) if row.default_category_id else None,
             "is_favorite": row.is_favorite, "created_at": iso(row.created_at)}
            for row in payees
        ],
        "monthly_budgets": list(MonthlyBudget.objects.filter(user=user).values(
            "period_month", "limit_paise", "is_recurring", "created_at", "updated_at"
        )),
        "category_budgets": [
            {"public_id": str(row.public_id), "category_public_id": str(row.category.public_id),
             "period_month": iso(row.period_month), "limit_paise": row.limit_paise,
             "alert_threshold": row.alert_threshold, "is_recurring": row.is_recurring}
            for row in CategoryBudget.objects.filter(user=user).select_related("category").order_by("id")
        ],
        "notifications": [
            {"public_id": str(row.public_id), "type": row.type, "severity": row.severity,
             "title": row.title, "body": row.body, "deep_link": row.deep_link,
             "data": row.data, "read_at": iso(row.read_at), "created_at": iso(row.created_at)}
            for row in notifications
        ],
        "support_issues": [
            {"public_id": str(row.public_id), "subject": row.subject,
             "description": row.description, "status": row.status,
             "created_at": iso(row.created_at), "resolved_at": iso(row.resolved_at)}
            for row in issue_reports
        ],
        "privacy_requests": [
            {"type": row.type, "status": row.status, "scheduled_for": iso(row.scheduled_for),
             "created_at": iso(row.created_at), "completed_at": iso(row.completed_at)}
            for row in data_requests
        ],
        "login_sessions": [
            {"device_label": row.device_label, "user_agent": row.user_agent,
             "ip_address": row.ip_address, "created_at": iso(row.created_at),
             "last_active_at": iso(row.last_active_at), "expires_at": iso(row.expires_at),
             "revoked_at": iso(row.revoked_at)}
            for row in sessions
        ],
        "two_factor_methods": [
            {"method": row.method, "enabled": bool(row.enabled_at),
             "enabled_at": iso(row.enabled_at), "created_at": iso(row.created_at)}
            for row in TwoFactorMethod.objects.filter(user=user).order_by("id")
        ],
        "audit_events": [
            {"action": row.action, "entity_type": row.entity_type,
             "entity_id": row.entity_id, "ip_address": row.ip_address,
             "metadata": row.metadata, "created_at": iso(row.created_at)}
            for row in audit_events
        ],
    }


@transaction.atomic
def process_due_account_deletion(request_id, *, now=None):
    """Erase an account after its grace period, preserving a minimal audit event."""
    now = now or timezone.now()
    user_id = DataRequest.objects.filter(
        pk=request_id, type=DataRequest.RequestType.DELETE_ACCOUNT
    ).values_list("user_id", flat=True).first()
    if user_id is None:
        return "skipped"

    user = User.objects.select_for_update().filter(pk=user_id).first()
    if user is None:
        return "skipped"
    request = DataRequest.objects.select_for_update().filter(
        pk=request_id,
        user=user,
        type=DataRequest.RequestType.DELETE_ACCOUNT,
        status=DataRequest.Status.REQUESTED,
        scheduled_for__lte=now,
    )
    request = request.first()
    if request is None:
        return "skipped"
    unresolved_count = Payment.objects.filter(
        user=user,
        status__in=(Payment.Status.INITIATED, Payment.Status.PROCESSING, Payment.Status.UNKNOWN),
    ).count()
    if unresolved_count:
        request.scheduled_for = now + timedelta(days=1)
        request.save(update_fields=("scheduled_for",))
        record_audit(
            user,
            "account_deletion_deferred",
            entity_type="data_request",
            entity_id=request.pk,
            metadata={"unresolved_payments": unresolved_count},
        )
        return "deferred"

    export_ids = list(
        DataRequest.objects.filter(
            user=user, type=DataRequest.RequestType.EXPORT
        ).values_list("id", flat=True)
    )
    export_root = Path(settings.PRIVATE_EXPORT_ROOT)
    for export_id in export_ids:
        (export_root / f"request-{export_id}.json").unlink(missing_ok=True)

    # Expense.category uses RESTRICT in MySQL. Remove the user's expenses first
    # so the subsequent user/category cascades cannot be blocked by that FK.
    Expense.objects.filter(user=user).delete()
    AuditLog.objects.filter(user=user).update(ip_address=None, metadata=None)
    record_audit(
        None,
        "account_deleted",
        entity_type="data_request",
        entity_id=request.pk,
        metadata={"grace_period_days": DELETION_GRACE_DAYS},
    )
    user.delete()
    return "deleted"
