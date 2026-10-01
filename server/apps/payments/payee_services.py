"""Transactional operations for saved payees."""

from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound, ValidationError

from apps.categories.models import Category
from apps.payments.models import Payee


def _category_for_user(user, public_id):
    if public_id is None:
        return None
    category = Category.objects.filter(public_id=public_id, archived_at__isnull=True).filter(
        Q(user__isnull=True) | Q(user=user)
    ).first()
    if category is None:
        raise ValidationError({"default_category_public_id": "Choose an available category."})
    return category


@transaction.atomic
def create_payee(user, values):
    data = dict(values)
    category_id = data.pop("default_category_public_id", None)
    data["default_category"] = _category_for_user(user, category_id)
    data["user"] = user
    try:
        return Payee.objects.create(**data)
    except IntegrityError as exc:
        raise ValidationError({"upi_id": "A saved payee already uses this UPI ID."}) from exc


@transaction.atomic
def update_payee(user, payee, values):
    data = dict(values)
    if "default_category_public_id" in data:
        data["default_category"] = _category_for_user(
            user, data.pop("default_category_public_id")
        )
    for field, value in data.items():
        setattr(payee, field, value)
    try:
        payee.save(update_fields=tuple(data))
    except IntegrityError as exc:
        raise ValidationError({"upi_id": "A saved payee already uses this UPI ID."}) from exc
    return payee


def require_payee(user, public_id):
    payee = Payee.objects.filter(user=user, public_id=public_id).select_related(
        "default_category"
    ).first()
    if payee is None:
        raise NotFound("Saved payee was not found.")
    return payee


def delete_payee(user, payee):
    Payee.objects.filter(user=user, pk=payee.pk).delete()
