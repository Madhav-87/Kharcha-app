"""Analytics API query and response serializers."""

from rest_framework import serializers

MAX_PAISE = 18_446_744_073_709_551_615


class DashboardQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=90, required=False, default=7)


class MonthlyTrendQuerySerializer(serializers.Serializer):
    months = serializers.IntegerField(min_value=1, max_value=24, required=False, default=6)


class PeriodMonthQuerySerializer(serializers.Serializer):
    period_month = serializers.DateField(required=False)

    def validate_period_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError("Use the first day of the reporting month.")
        return value


class SummarySerializer(serializers.Serializer):
    today_spent_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE)
    today_transaction_count = serializers.IntegerField(min_value=0)
    month_spent_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE)
    month_transaction_count = serializers.IntegerField(min_value=0)


class DailyTrendSerializer(serializers.Serializer):
    day = serializers.DateField()
    total_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE)
    txn_count = serializers.IntegerField(min_value=0)


class CategoryBreakdownSerializer(serializers.Serializer):
    category_public_id = serializers.UUIDField()
    category_name = serializers.CharField()
    icon = serializers.CharField()
    emoji = serializers.CharField(allow_null=True)
    color = serializers.CharField()
    total_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE)
    transaction_count = serializers.IntegerField(min_value=0)
    share_percent = serializers.FloatField(min_value=0, max_value=100)


class BudgetUsageSerializer(serializers.Serializer):
    limit_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    spent_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE)
    remaining_paise = serializers.IntegerField()
    pct_used = serializers.FloatField(min_value=0)


class CategoryBudgetUsageSerializer(BudgetUsageSerializer):
    category_public_id = serializers.UUIDField()
    category_name = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()
    alert_threshold = serializers.IntegerField(min_value=1, max_value=100, allow_null=True)


class RecentExpenseSerializer(serializers.Serializer):
    public_id = serializers.UUIDField()
    title = serializers.CharField()
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    status = serializers.CharField()
    method = serializers.CharField()
    source = serializers.CharField()
    expense_at = serializers.DateTimeField()
    category_public_id = serializers.UUIDField()
    category_name = serializers.CharField()
    category_color = serializers.CharField()


class DashboardSerializer(serializers.Serializer):
    date = serializers.DateField()
    period_month = serializers.DateField()
    summary = SummarySerializer()
    daily_trend = DailyTrendSerializer(many=True)
    monthly_budget = BudgetUsageSerializer(allow_null=True)
    category_breakdown = CategoryBreakdownSerializer(many=True)
    category_budgets = CategoryBudgetUsageSerializer(many=True)
    recent_expenses = RecentExpenseSerializer(many=True)


class BudgetUsageResponseSerializer(serializers.Serializer):
    period_month = serializers.DateField()
    monthly_budget = BudgetUsageSerializer(allow_null=True)
    category_budgets = CategoryBudgetUsageSerializer(many=True)


class MonthlyTrendItemSerializer(serializers.Serializer):
    month = serializers.DateField()
    total_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE)
    transaction_count = serializers.IntegerField(min_value=0)
