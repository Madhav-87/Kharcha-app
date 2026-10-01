"""Serializers for manual expenses."""

from rest_framework import serializers

from apps.expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    category_public_id = serializers.UUIDField(source="category.public_id", read_only=True)
    payee_public_id = serializers.UUIDField(source="payee.public_id", read_only=True, allow_null=True)

    class Meta:
        model = Expense
        fields = ("public_id", "title", "amount_paise", "note", "method", "status", "source", "expense_at", "category_public_id", "payee_public_id", "created_at", "updated_at")
        read_only_fields = fields


class ManualExpenseCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=160, trim_whitespace=True)
    amount_paise = serializers.IntegerField(min_value=1, max_value=18_446_744_073_709_551_615)
    category_public_id = serializers.UUIDField()
    payee_public_id = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    method = serializers.ChoiceField(choices=Expense.Method.choices, default=Expense.Method.UPI)
    status = serializers.ChoiceField(choices=Expense.Status.choices, default=Expense.Status.PAID)
    expense_at = serializers.DateTimeField(required=False)


class ManualExpenseUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    amount_paise = serializers.IntegerField(min_value=1, max_value=18_446_744_073_709_551_615, required=False)
    category_public_id = serializers.UUIDField(required=False)
    payee_public_id = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    method = serializers.ChoiceField(choices=Expense.Method.choices, required=False)
    status = serializers.ChoiceField(choices=Expense.Status.choices, required=False)
    expense_at = serializers.DateTimeField(required=False)
