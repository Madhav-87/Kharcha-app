from django.urls import path

from apps.analytics.views import (
    BudgetUsageView,
    CategoryBreakdownView,
    DashboardView,
    MonthlyTrendView,
)

app_name = "analytics"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("trends/", MonthlyTrendView.as_view(), name="trends"),
    path("categories/", CategoryBreakdownView.as_view(), name="category-breakdown"),
    path("budget-usage/", BudgetUsageView.as_view(), name="budget-usage"),
]
