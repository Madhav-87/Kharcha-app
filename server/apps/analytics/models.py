"""Read-only Django mappings for the supplied MySQL reporting views."""

from django.db import models

from apps.accounts.models import User
from apps.categories.models import Category
from common.db_fields import UnsignedBigIntegerField, UnsignedTinyIntegerField


class DailySpend(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column="user_id")
    day = models.DateField()
    total_paise = UnsignedBigIntegerField()
    txn_count = UnsignedBigIntegerField()
    pk = models.CompositePrimaryKey("user_id", "day")

    class Meta:
        managed = False
        db_table = "v_daily_spend"


class CategorySpendMonthly(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column="user_id")
    category = models.ForeignKey(
        Category, on_delete=models.DO_NOTHING, db_column="category_id"
    )
    month = models.DateField()
    total_paise = UnsignedBigIntegerField()
    txn_count = UnsignedBigIntegerField()
    pk = models.CompositePrimaryKey("user_id", "category_id", "month")

    class Meta:
        managed = False
        db_table = "v_category_spend_monthly"


class MonthlyBudgetUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column="user_id")
    period_month = models.DateField()
    limit_paise = UnsignedBigIntegerField()
    spent_paise = UnsignedBigIntegerField()
    remaining_paise = UnsignedBigIntegerField()
    pct_used = models.DecimalField(max_digits=6, decimal_places=1)
    pk = models.CompositePrimaryKey("user_id", "period_month")

    class Meta:
        managed = False
        db_table = "v_monthly_budget_usage"


class CategoryBudgetUsage(models.Model):
    budget_id = UnsignedBigIntegerField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column="user_id")
    category = models.ForeignKey(
        Category, on_delete=models.DO_NOTHING, db_column="category_id"
    )
    period_month = models.DateField()
    limit_paise = UnsignedBigIntegerField()
    alert_threshold = UnsignedTinyIntegerField(null=True, blank=True)
    spent_paise = UnsignedBigIntegerField()
    remaining_paise = UnsignedBigIntegerField()
    pct_used = models.DecimalField(max_digits=6, decimal_places=1)

    class Meta:
        managed = False
        db_table = "v_category_budget_usage"
