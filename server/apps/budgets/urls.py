from django.urls import path

from apps.budgets.views import (
    CategoryBudgetDetailView,
    CategoryBudgetListCreateView,
    MonthlyBudgetView,
)

urlpatterns = [
    path("monthly/", MonthlyBudgetView.as_view(), name="monthly-budget"),
    path("categories/", CategoryBudgetListCreateView.as_view(), name="category-budget-list-create"),
    path("categories/<uuid:public_id>/", CategoryBudgetDetailView.as_view(), name="category-budget-detail"),
]
