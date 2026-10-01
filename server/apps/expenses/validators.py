"""Validation helpers for the manual expense API."""

from rest_framework import serializers

from apps.expenses.models import Expense


class ExpenseFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, max_length=120)
    category_public_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=Expense.Status.choices, required=False)
    method = serializers.ChoiceField(choices=Expense.Method.choices, required=False)
    source = serializers.ChoiceField(choices=Expense.Source.choices, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    min_amount_paise = serializers.IntegerField(required=False, min_value=1)
    max_amount_paise = serializers.IntegerField(required=False, min_value=1)
    ordering = serializers.ChoiceField(choices=("-expense_at", "expense_at", "-amount_paise", "amount_paise", "title"), required=False, default="-expense_at")
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)

    def validate(self, attrs):
        if attrs.get("date_from") and attrs.get("date_to") and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError({"date_to": "Must be on or after date_from."})
        if attrs.get("min_amount_paise") is not None and attrs.get("max_amount_paise") is not None and attrs["min_amount_paise"] > attrs["max_amount_paise"]:
            raise serializers.ValidationError({"max_amount_paise": "Must be at least min_amount_paise."})
        return attrs
