"""Budget threshold notification creation and deduplication."""

from django.db import IntegrityError, transaction

from apps.accounts.models import UserSettings
from apps.budgets.models import CategoryBudget, MonthlyBudget
from apps.budgets.selectors import expense_totals, normalize_month
from apps.notifications.models import Notification


def _create_notification(user, *, notification_type, severity, title, body, dedupe_key, data, category_budget=None):
    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                type=notification_type,
                severity=severity,
                title=title,
                body=body,
                deep_link="/budgets",
                data=data,
                category_budget=category_budget,
                dedupe_key=dedupe_key,
            )
            from apps.notifications.services import queue_notification_delivery

            queue_notification_delivery(notification)
            return notification
    except IntegrityError:
        # Another expense or budget update already emitted this period's alert.
        notification = Notification.objects.filter(user=user, dedupe_key=dedupe_key).first()
        if notification:
            from apps.notifications.services import queue_notification_delivery

            queue_notification_delivery(notification)
            return None
        raise


@transaction.atomic
def evaluate_budget_alerts(user, period_month, *, category_ids=None):
    """Emit at most one notification per budget threshold and month."""
    month = normalize_month(period_month)
    settings_obj = UserSettings.objects.filter(user=user).first()
    if settings_obj is not None and not settings_obj.notify_budget_alerts:
        return []
    default_threshold = settings_obj.budget_alert_threshold if settings_obj else 80
    spent, category_totals = expense_totals(user, month)
    notifications = []

    monthly_budget = MonthlyBudget.objects.filter(user=user, period_month=month).first()
    if monthly_budget:
        notifications.extend(_evaluate_one(
            user,
            month=month,
            spent=spent,
            limit=monthly_budget.limit_paise,
            threshold=default_threshold,
            identifier=f"monthly:{month.isoformat()}",
            title_prefix="Monthly budget",
            budget_public_id=None,
        ))

    category_budgets = CategoryBudget.objects.filter(user=user, period_month=month).select_related("category")
    if category_ids is not None:
        category_budgets = category_budgets.filter(category_id__in=category_ids)
    for budget in category_budgets:
        notifications.extend(_evaluate_one(
            user,
            month=month,
            spent=category_totals.get(budget.category_id, 0),
            limit=budget.limit_paise,
            threshold=budget.alert_threshold or default_threshold,
            identifier=f"category:{budget.public_id}",
            title_prefix=f"{budget.category.name} budget",
            budget_public_id=str(budget.public_id),
            category_budget=budget,
        ))
    return notifications


def _evaluate_one(
    user, *, month, spent, limit, threshold, identifier, title_prefix,
    budget_public_id, category_budget=None,
):
    if limit <= 0:
        return []
    crossed = []
    if threshold < 100 and spent * 100 >= limit * threshold:
        crossed.append((
            "threshold", Notification.Type.BUDGET_THRESHOLD, Notification.Severity.WARNING,
            f"{title_prefix} at {threshold}%",
            f"You have spent {spent:,} paise of your {limit:,} paise budget for {month:%B %Y}.",
        ))
    if spent >= limit:
        crossed.append((
            "exceeded", Notification.Type.BUDGET_EXCEEDED, Notification.Severity.ERROR,
            f"{title_prefix} reached",
            f"You have spent {spent:,} paise against your {limit:,} paise budget for {month:%B %Y}.",
        ))
    created = []
    for suffix, kind, severity, title, body in crossed:
        notification = _create_notification(
            user,
            notification_type=kind,
            severity=severity,
            title=title,
            body=body,
            dedupe_key=f"budget:{identifier}:{month:%Y-%m}:{suffix}",
            data={"budget_public_id": budget_public_id, "period_month": month.isoformat(), "spent_paise": spent, "limit_paise": limit},
            category_budget=category_budget,
        )
        if notification is not None:
            created.append(notification)
    return created
