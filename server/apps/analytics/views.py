"""Authenticated, user-scoped analytics endpoints."""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.analytics import selectors, services
from apps.analytics.serializers import (
    BudgetUsageResponseSerializer,
    DashboardQuerySerializer,
    DashboardSerializer,
    MonthlyTrendItemSerializer,
    MonthlyTrendQuerySerializer,
    PeriodMonthQuerySerializer,
    CategoryBreakdownSerializer,
)


def _success(data):
    return {"success": True, "data": data, "message": ""}


def _query(serializer_class, query_params):
    serializer = serializer_class(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _month(query_params):
    data = _query(PeriodMonthQuerySerializer, query_params)
    return data.get("period_month") or selectors.month_start(selectors.ist_today())


class DashboardView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        params = _query(DashboardQuerySerializer, request.query_params)
        data = services.dashboard(request.user, days=params["days"])
        return Response(_success(DashboardSerializer(data).data))


class MonthlyTrendView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        params = _query(MonthlyTrendQuerySerializer, request.query_params)
        data = services.monthly_trend(request.user, months=params["months"])
        return Response(_success(MonthlyTrendItemSerializer(data, many=True).data))


class CategoryBreakdownView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        period_month = _month(request.query_params)
        data = services.category_breakdown(request.user, period_month)
        return Response(_success(CategoryBreakdownSerializer(data, many=True).data))


class BudgetUsageView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        period_month = _month(request.query_params)
        data = services.budget_usage(request.user, period_month)
        return Response(_success(BudgetUsageResponseSerializer(data).data))
