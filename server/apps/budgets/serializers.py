"""Budget API serializers."""

from rest_framework import serializers

from apps.budgets.models import CategoryBudget

MAX_PAISE = 18_446_744_073_709_551_615


class MonthlyBudgetWriteSerializer(serializers.Serializer):
    period_month = serializers.DateField()
    limit_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    is_recurring = serializers.BooleanField(required=False, default=True)

    def validate_period_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError("Use the first day of the budget month.")
        return value


class CategoryBudgetCreateSerializer(serializers.Serializer):
    category_public_id = serializers.UUIDField()
    period_month = serializers.DateField()
    limit_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    alert_threshold = serializers.IntegerField(min_value=1, max_value=100, required=False, allow_null=True)
    is_recurring = serializers.BooleanField(required=False, default=True)

    def validate_period_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError("Use the first day of the budget month.")
        return value


class CategoryBudgetUpdateSerializer(serializers.Serializer):
    limit_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE, required=False)
    alert_threshold = serializers.IntegerField(min_value=1, max_value=100, required=False, allow_null=True)
    is_recurring = serializers.BooleanField(required=False)


class CategoryBudgetSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    category_public_id = serializers.UUIDField(source="category.public_id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    spent_paise = serializers.IntegerField(read_only=True)
    remaining_paise = serializers.IntegerField(read_only=True)
    pct_used = serializers.DecimalField(max_digits=30, decimal_places=1, read_only=True)

    class Meta:
        model = CategoryBudget
        fields = (
            "public_id", "category_public_id", "category_name", "period_month", "limit_paise",
            "alert_threshold", "is_recurring", "spent_paise", "remaining_paise", "pct_used",
        )
