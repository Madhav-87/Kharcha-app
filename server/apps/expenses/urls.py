from django.urls import path

from apps.expenses.views import ExpenseDetailView, ExpenseListCreateView

urlpatterns = [
    path("", ExpenseListCreateView.as_view(), name="expense-list-create"),
    path("<uuid:public_id>/", ExpenseDetailView.as_view(), name="expense-detail"),
]
