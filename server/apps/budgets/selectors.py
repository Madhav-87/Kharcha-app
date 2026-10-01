"""Budget read queries and usage calculations."""

from calendar import monthrange
from datetime import date

from django.db.models import Sum
from rest_framework.exceptions import NotFound

from apps.budgets.models import CategoryBudget, MonthlyBudget
from apps.expenses.models import Expense


def normalize_month(value):
    return date(value.year, value.month, 1)


def month_bounds(period_month):
    start = normalize_month(period_month)
    end = date(start.year, start.month, monthrange(start.year, start.month)[1])
    return start, end


def expense_totals(user, period_month):
    start, end = month_bounds(period_month)
    expenses = Expense.objects.filter(
        user=user, status=Expense.Status.PAID, deleted_at__isnull=True,
        expense_at__date__gte=start, expense_at__date__lte=end,
    )
    total = expenses.aggregate(total=Sum("amount_paise"))["total"] or 0
    category_totals = {
        row["category_id"]: row["total"] or 0
        for row in expenses.values("category_id").annotate(total=Sum("amount_paise"))
    }
    return total, category_totals


def monthly_budget_usage(user, period_month):
    month = normalize_month(period_month)
    budget = MonthlyBudget.objects.filter(user=user, period_month=month).first()
    spent, _ = expense_totals(user, month)
    limit = budget.limit_paise if budget else None
    return {
        "period_month": month,
        "limit_paise": limit,
        "spent_paise": spent,
        "remaining_paise": max(limit - spent, 0) if limit is not None else None,
        "pct_used": round((spent * 100 / limit), 1) if limit else None,
        "is_recurring": budget.is_recurring if budget else None,
    }


def list_category_budgets(user, period_month):
    month = normalize_month(period_month)
    budgets = list(
        CategoryBudget.objects.filter(user=user, period_month=month)
        .select_related("category").order_by("category__name", "pk")
    )
    _, totals = expense_totals(user, month)
    for budget in budgets:
        spent = totals.get(budget.category_id, 0)
        budget.spent_paise = spent
        budget.remaining_paise = max(budget.limit_paise - spent, 0)
        budget.pct_used = round(spent * 100 / budget.limit_paise, 1)
    return budgets


def get_category_budget(user, public_id):
    budget = CategoryBudget.objects.filter(user=user, public_id=public_id).select_related(
        "category"
    ).first()
    if budget is None:
        raise NotFound("Category budget was not found.")
    _, totals = expense_totals(user, budget.period_month)
    spent = totals.get(budget.category_id, 0)
    budget.spent_paise = spent
    budget.remaining_paise = max(budget.limit_paise - spent, 0)
    budget.pct_used = round(spent * 100 / budget.limit_paise, 1)
    return budget
