"""Read-only analytics use cases."""

from apps.analytics import selectors


def dashboard(user, *, days=7):
    return selectors.get_dashboard(user, days=days)


def monthly_trend(user, *, months=6):
    return selectors.get_monthly_trend(user, months=months)


def category_breakdown(user, period_month):
    return selectors.get_category_breakdown(user, period_month)


def budget_usage(user, period_month):
    return selectors.get_budget_usage(user, period_month)
