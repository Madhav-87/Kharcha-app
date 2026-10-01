"""Manual expense write operations."""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.categories.models import Category
from apps.expenses.models import Expense
from apps.payments.models import Payee


def _category_for_user(user, public_id):
    category = Category.objects.filter(
        public_id=public_id, archived_at__isnull=True
    ).filter(Q(user__isnull=True) | Q(user=user)).first()
    if category is None:
        raise ValidationError({"category_public_id": "Choose an available category."})
    return category


def _payee_for_user(user, public_id):
    if public_id is None:
        return None
    payee = Payee.objects.filter(user=user, public_id=public_id).first()
    if payee is None:
        raise ValidationError({"payee_public_id": "Choose one of your saved payees."})
    return payee


@transaction.atomic
def create_manual_expense(user, values):
    data = dict(values)
    category = _category_for_user(user, data.pop("category_public_id"))
    payee = _payee_for_user(user, data.pop("payee_public_id", None))
    return Expense.objects.create(
        user=user,
        category=category,
        payee=payee,
        source=Expense.Source.MANUAL,
        **data,
    )


@transaction.atomic
def update_manual_expense(user, expense, values):
    if expense.source != Expense.Source.MANUAL or expense.payment_id is not None:
        raise PermissionDenied("Payment-linked expenses cannot be edited manually.")
    data = dict(values)
    if "category_public_id" in data:
        data["category"] = _category_for_user(user, data.pop("category_public_id"))
    if "payee_public_id" in data:
        data["payee"] = _payee_for_user(user, data.pop("payee_public_id"))
    for field, value in data.items():
        setattr(expense, field, value)
    if data:
        expense.save(update_fields=tuple(data))
    return expense


@transaction.atomic
def delete_manual_expense(user, expense):
    if expense.source != Expense.Source.MANUAL or expense.payment_id is not None:
        raise PermissionDenied("Payment-linked expenses cannot be deleted manually.")
    expense.deleted_at = timezone.now()
    expense.save(update_fields=("deleted_at",))
