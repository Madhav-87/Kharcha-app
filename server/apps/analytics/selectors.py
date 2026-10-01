"""User-scoped analytics queries over the schema's IST reporting views."""

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Sum

from apps.analytics.models import (
    CategoryBudgetUsage,
    CategorySpendMonthly,
    DailySpend,
    MonthlyBudgetUsage,
)
from apps.expenses.models import Expense


IST = ZoneInfo("Asia/Kolkata")


def ist_today():
    from django.utils import timezone

    return timezone.now().astimezone(IST).date()


def month_start(value):
    return date(value.year, value.month, 1)


def shift_month(value, offset):
    month_index = value.year * 12 + value.month - 1 + offset
    year, month_zero = divmod(month_index, 12)
    return date(year, month_zero + 1, 1)


def get_dashboard(user, *, days=7):
    today = ist_today()
    current_month = month_start(today)
    daily_rows = list(
        DailySpend.objects.filter(
            user=user,
            day__gte=today - timedelta(days=days - 1),
            day__lte=today,
        ).order_by("day")
    )
    daily_by_day = {row.day: row for row in daily_rows}
    daily_trend = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        row = daily_by_day.get(day)
        daily_trend.append(
            {
                "day": day,
                "total_paise": int(row.total_paise) if row else 0,
                "txn_count": int(row.txn_count) if row else 0,
            }
        )

    today_row = daily_by_day.get(today)
    month_totals = DailySpend.objects.filter(
        user=user, day__gte=current_month, day__lte=today
    ).aggregate(total=Sum("total_paise"), count=Sum("txn_count"))
    categories = get_category_breakdown(user, current_month)
    category_budgets = get_category_budget_usage(user, current_month)
    monthly_budget = MonthlyBudgetUsage.objects.filter(
        user=user, period_month=current_month
    ).first()
    recent_expenses = list(
        Expense.objects.filter(user=user, deleted_at__isnull=True)
        .select_related("category")
        .order_by("-expense_at", "-pk")[:5]
    )

    return {
        "date": today,
        "period_month": current_month,
        "summary": {
            "today_spent_paise": int(today_row.total_paise) if today_row else 0,
            "today_transaction_count": int(today_row.txn_count) if today_row else 0,
            "month_spent_paise": int(month_totals["total"] or 0),
            "month_transaction_count": int(month_totals["count"] or 0),
        },
        "daily_trend": daily_trend,
        "monthly_budget": _monthly_budget_data(monthly_budget),
        "category_breakdown": categories,
        "category_budgets": category_budgets,
        "recent_expenses": [_expense_row(expense) for expense in recent_expenses],
    }


def get_category_breakdown(user, period_month):
    month = month_start(period_month)
    rows = list(
        CategorySpendMonthly.objects.filter(user=user, month=month)
        .select_related("category")
        .order_by("-total_paise", "category__name")
    )
    total = sum(int(row.total_paise) for row in rows)
    return [
        {
            "category_public_id": str(row.category.public_id),
            "category_name": row.category.name,
            "icon": row.category.icon,
            "emoji": row.category.emoji,
            "color": row.category.color,
            "total_paise": int(row.total_paise),
            "transaction_count": int(row.txn_count),
            "share_percent": (
                round(int(row.total_paise) * 100 / total, 1) if total else 0.0
            ),
        }
        for row in rows
    ]


def get_monthly_trend(user, *, months=6):
    current_month = month_start(ist_today())
    first_month = shift_month(current_month, -(months - 1))
    rows = (
        CategorySpendMonthly.objects.filter(
            user=user, month__gte=first_month, month__lte=current_month
        )
        .values("month")
        .annotate(total=Sum("total_paise"), transaction_count=Sum("txn_count"))
        .order_by("month")
    )
    totals = {
        row["month"]: (int(row["total"] or 0), int(row["transaction_count"] or 0))
        for row in rows
    }
    return [
        {
            "month": month,
            "total_paise": totals.get(month, (0, 0))[0],
            "transaction_count": totals.get(month, (0, 0))[1],
        }
        for month in (
            shift_month(current_month, offset)
            for offset in range(-(months - 1), 1)
        )
    ]


def get_category_budget_usage(user, period_month):
    month = month_start(period_month)
    rows = CategoryBudgetUsage.objects.filter(
        user=user, period_month=month
    ).select_related("category").order_by("category__name", "budget_id")
    return [
        {
            "category_public_id": str(row.category.public_id),
            "category_name": row.category.name,
            "icon": row.category.icon,
            "color": row.category.color,
            "limit_paise": int(row.limit_paise),
            "spent_paise": int(row.spent_paise),
            "remaining_paise": int(row.remaining_paise),
            "pct_used": float(row.pct_used),
            "alert_threshold": row.alert_threshold,
        }
        for row in rows
    ]


def get_budget_usage(user, period_month):
    month = month_start(period_month)
    monthly_budget = MonthlyBudgetUsage.objects.filter(
        user=user, period_month=month
    ).first()
    return {
        "period_month": month,
        "monthly_budget": _monthly_budget_data(monthly_budget),
        "category_budgets": get_category_budget_usage(user, month),
    }


def _monthly_budget_data(row):
    if row is None:
        return None
    return {
        "limit_paise": int(row.limit_paise),
        "spent_paise": int(row.spent_paise),
        "remaining_paise": int(row.remaining_paise),
        "pct_used": float(row.pct_used),
    }


def _expense_row(expense):
    return {
        "public_id": str(expense.public_id),
        "title": expense.title,
        "amount_paise": int(expense.amount_paise),
        "status": expense.status,
        "method": expense.method,
        "source": expense.source,
        "expense_at": expense.expense_at,
        "category_public_id": str(expense.category.public_id),
        "category_name": expense.category.name,
        "category_color": expense.category.color,
    }
