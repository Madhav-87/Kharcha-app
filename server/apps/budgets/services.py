"""Transactional budget management operations."""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.budgets import alerts
from apps.budgets.models import CategoryBudget, MonthlyBudget
from apps.budgets.selectors import normalize_month
from apps.categories.models import Category
from django.db.models import Q


def _category_for_user(user, public_id):
    category = Category.objects.filter(public_id=public_id, archived_at__isnull=True).filter(
        Q(user__isnull=True) | Q(user=user)
    ).first()
    if category is None:
        raise ValidationError({"category_public_id": "Choose an available category."})
    return category


@transaction.atomic
def save_monthly_budget(user, values):
    month = normalize_month(values["period_month"])
    budget = MonthlyBudget.objects.filter(user=user, period_month=month).first()
    if budget is None:
        try:
            with transaction.atomic():
                budget = MonthlyBudget.objects.create(
                    user=user,
                    period_month=month,
                    limit_paise=values["limit_paise"],
                    is_recurring=values.get("is_recurring", True),
                )
        except IntegrityError:
            budget = MonthlyBudget.objects.get(user=user, period_month=month)
    else:
        budget.limit_paise = values["limit_paise"]
        budget.is_recurring = values.get("is_recurring", budget.is_recurring)
        budget.save(update_fields=("limit_paise", "is_recurring", "updated_at"))
    alerts.evaluate_budget_alerts(user, month)
    return budget


@transaction.atomic
def create_category_budget(user, values):
    category = _category_for_user(user, values["category_public_id"])
    month = normalize_month(values["period_month"])
    try:
        budget = CategoryBudget.objects.create(
            user=user,
            category=category,
            period_month=month,
            limit_paise=values["limit_paise"],
            alert_threshold=values.get("alert_threshold"),
            is_recurring=values.get("is_recurring", True),
        )
    except IntegrityError as exc:
        raise ValidationError({"category_public_id": "A budget already exists for this category and month."}) from exc
    alerts.evaluate_budget_alerts(user, month, category_ids=[category.pk])
    return budget


@transaction.atomic
def update_category_budget(user, budget, values):
    for field in ("limit_paise", "alert_threshold", "is_recurring"):
        if field in values:
            setattr(budget, field, values[field])
    try:
        budget.save(update_fields=tuple(values) + ("updated_at",))
    except IntegrityError as exc:
        raise ValidationError("The category budget could not be updated.") from exc
    alerts.evaluate_budget_alerts(user, budget.period_month, category_ids=[budget.category_id])
    return budget


@transaction.atomic
def delete_category_budget(user, budget):
    CategoryBudget.objects.filter(user=user, pk=budget.pk).delete()


@transaction.atomic
def delete_monthly_budget(user, period_month):
    month = normalize_month(period_month)
    deleted, _ = MonthlyBudget.objects.filter(user=user, period_month=month).delete()
    if not deleted:
        raise NotFound("Monthly budget was not found.")
