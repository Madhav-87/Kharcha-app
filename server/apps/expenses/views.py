"""Manual expense CRUD and filtered expense listing endpoints."""

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.expenses import selectors, services
from apps.expenses.serializers import (
    ExpenseSerializer,
    ManualExpenseCreateSerializer,
    ManualExpenseUpdateSerializer,
)
from apps.expenses.validators import ExpenseFilterSerializer


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


class ExpenseListCreateView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        serializer = ExpenseFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        queryset = selectors.filter_expenses(request.user, filters)
        paginator = Paginator(queryset, filters["page_size"])
        try:
            page = paginator.page(filters["page"])
        except (EmptyPage, PageNotAnInteger) as exc:
            raise ValidationError({"page": "No expenses exist on this page."}) from exc
        return Response(_success({
            "results": ExpenseSerializer(page.object_list, many=True).data,
            "pagination": {
                "page": page.number,
                "page_size": filters["page_size"],
                "total": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
            },
        }))

    def post(self, request):
        serializer = ManualExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = services.create_manual_expense(request.user, serializer.validated_data)
        expense = selectors.get_expense(request.user, expense.public_id)
        return Response(
            _success(ExpenseSerializer(expense).data, "Expense created."),
            status=status.HTTP_201_CREATED,
        )


class ExpenseDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, public_id):
        expense = selectors.get_expense(request.user, public_id)
        return Response(_success(ExpenseSerializer(expense).data))

    def patch(self, request, public_id):
        expense = selectors.get_expense(request.user, public_id)
        serializer = ManualExpenseUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        expense = services.update_manual_expense(request.user, expense, serializer.validated_data)
        expense = selectors.get_expense(request.user, expense.public_id)
        return Response(_success(ExpenseSerializer(expense).data, "Expense updated."))

    def delete(self, request, public_id):
        expense = selectors.get_expense(request.user, public_id)
        services.delete_manual_expense(request.user, expense)
        return Response(_success({}, "Expense deleted."))
