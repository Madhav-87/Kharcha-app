"""User-scoped expense reads and filters."""

from django.db.models import Q
from rest_framework.exceptions import NotFound

from apps.expenses.models import Expense


def filter_expenses(user, filters):
    queryset = Expense.objects.filter(user=user, deleted_at__isnull=True).select_related(
        "category", "payee"
    )
    if filters.get("category_public_id"):
        queryset = queryset.filter(category__public_id=filters["category_public_id"])
    if filters.get("status"):
        queryset = queryset.filter(status=filters["status"])
    if filters.get("method"):
        queryset = queryset.filter(method=filters["method"])
    if filters.get("source"):
        queryset = queryset.filter(source=filters["source"])
    if filters.get("date_from"):
        queryset = queryset.filter(expense_at__date__gte=filters["date_from"])
    if filters.get("date_to"):
        queryset = queryset.filter(expense_at__date__lte=filters["date_to"])
    if filters.get("min_amount_paise") is not None:
        queryset = queryset.filter(amount_paise__gte=filters["min_amount_paise"])
    if filters.get("max_amount_paise") is not None:
        queryset = queryset.filter(amount_paise__lte=filters["max_amount_paise"])
    if filters.get("search"):
        term = filters["search"].strip()
        queryset = queryset.filter(Q(title__icontains=term) | Q(note__icontains=term) | Q(payee__name__icontains=term))
    return queryset.order_by(filters.get("ordering", "-expense_at"), "-pk")


def get_expense(user, public_id):
    expense = Expense.objects.filter(
        user=user, public_id=public_id, deleted_at__isnull=True
    ).select_related("category", "payee").first()
    if expense is None:
        raise NotFound("Expense was not found.")
    return expense
