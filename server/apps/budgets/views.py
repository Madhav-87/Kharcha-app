"""Budget CRUD and current usage endpoints."""

from datetime import date

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.budgets import selectors, services
from apps.budgets.serializers import (
    CategoryBudgetCreateSerializer,
    CategoryBudgetSerializer,
    CategoryBudgetUpdateSerializer,
    MonthlyBudgetWriteSerializer,
)


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


def _month_from_request(request, *, required=False):
    value = request.query_params.get("period_month")
    if value is None:
        if required:
            raise serializers.ValidationError({"period_month": "This query parameter is required."})
        today = timezone.localdate()
        return date(today.year, today.month, 1)
    field = serializers.DateField()
    try:
        month = field.run_validation(value)
    except serializers.ValidationError as exc:
        raise serializers.ValidationError({"period_month": exc.detail}) from exc
    if month.day != 1:
        raise serializers.ValidationError({"period_month": "Use the first day of the budget month."})
    return month


class MonthlyBudgetView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        month = _month_from_request(request)
        return Response(_success(selectors.monthly_budget_usage(request.user, month)))

    def put(self, request):
        serializer = MonthlyBudgetWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = services.save_monthly_budget(request.user, serializer.validated_data)
        return Response(_success(selectors.monthly_budget_usage(request.user, budget.period_month), "Monthly budget saved."))

    def delete(self, request):
        month = _month_from_request(request, required=True)
        services.delete_monthly_budget(request.user, month)
        return Response(_success({}, "Monthly budget deleted."))


class CategoryBudgetListCreateView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        month = _month_from_request(request)
        budgets = selectors.list_category_budgets(request.user, month)
        return Response(_success(CategoryBudgetSerializer(budgets, many=True).data))

    def post(self, request):
        serializer = CategoryBudgetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = services.create_category_budget(request.user, serializer.validated_data)
        budget = selectors.get_category_budget(request.user, budget.public_id)
        return Response(
            _success(CategoryBudgetSerializer(budget).data, "Category budget created."),
            status=status.HTTP_201_CREATED,
        )


class CategoryBudgetDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, public_id):
        budget = selectors.get_category_budget(request.user, public_id)
        return Response(_success(CategoryBudgetSerializer(budget).data))

    def patch(self, request, public_id):
        budget = selectors.get_category_budget(request.user, public_id)
        serializer = CategoryBudgetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        budget = services.update_category_budget(request.user, budget, serializer.validated_data)
        budget = selectors.get_category_budget(request.user, budget.public_id)
        return Response(_success(CategoryBudgetSerializer(budget).data, "Category budget updated."))

    def delete(self, request, public_id):
        budget = selectors.get_category_budget(request.user, public_id)
        services.delete_category_budget(request.user, budget)
        return Response(_success({}, "Category budget deleted."))
