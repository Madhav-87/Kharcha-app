"""Monthly and category budget records."""

from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.categories.models import Category
from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    PublicIdField,
    UnsignedBigAutoField,
    UnsignedBigIntegerField,
    UnsignedTinyIntegerField,
    UpdatedDateTime3Field,
)


class MonthlyBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="monthly_budgets")
    period_month = models.DateField()
    limit_paise = UnsignedBigIntegerField()
    is_recurring = models.BooleanField(default=True)
    created_at = DatabaseNowDateTime3Field()
    updated_at = UpdatedDateTime3Field()
    pk = models.CompositePrimaryKey("user_id", "period_month")

    class Meta:
        managed = False
        db_table = "monthly_budgets"
        constraints = [
            models.CheckConstraint(condition=Q(limit_paise__gt=0), name="chk_mb_limit")
        ]


class CategoryBudget(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category_budgets")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="budgets"
    )
    period_month = models.DateField()
    limit_paise = UnsignedBigIntegerField()
    alert_threshold = UnsignedTinyIntegerField(null=True, blank=True)
    is_recurring = models.BooleanField(default=True)
    created_at = DatabaseNowDateTime3Field()
    updated_at = UpdatedDateTime3Field()

    class Meta:
        managed = False
        db_table = "category_budgets"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "category", "period_month"), name="uq_cb_unique"
            ),
            models.CheckConstraint(condition=Q(limit_paise__gt=0), name="chk_cb_limit"),
            models.CheckConstraint(
                condition=(Q(alert_threshold__isnull=True) | Q(alert_threshold__range=(1, 100))),
                name="chk_cb_thr",
            ),
        ]
