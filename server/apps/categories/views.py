"""Category API views."""

from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories import selectors, services
from apps.categories.serializers import (
    CategoryCreateSerializer,
    CategoryPreferencesSerializer,
    CategorySerializer,
    CategoryUpdateSerializer,
)
from apps.accounts.permissions import IsActiveAccount


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


class CategoryListCreateView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        include_hidden = request.query_params.get("include_hidden", "true").lower() not in ("0", "false")
        return Response(_success(CategorySerializer(
            selectors.list_categories(request.user, include_hidden=include_hidden), many=True
        ).data))

    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            category = services.create_category(request.user, serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError({"name": "A category with these details already exists."}) from exc
        return Response(
            _success(CategorySerializer(category).data, "Category created."),
            status=status.HTTP_201_CREATED,
        )


class CategoryDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, public_id):
        category = services.get_category_for_user(request.user, public_id)
        preference = category.user_preferences.filter(user=request.user).first()
        category.user_category_preference = preference
        return Response(_success(CategorySerializer(category).data))

    def patch(self, request, public_id):
        category = services.get_category_for_user(request.user, public_id)
        serializer = CategoryUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = services.update_category(request.user, category, serializer.validated_data)
        return Response(_success(CategorySerializer(category).data, "Category updated."))

    def delete(self, request, public_id):
        category = services.get_category_for_user(request.user, public_id)
        services.archive_category(request.user, category)
        return Response(_success({}, "Category archived."))


class CategoryPreferencesView(APIView):
    permission_classes = [IsActiveAccount]

    def patch(self, request):
        serializer = CategoryPreferencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        categories = services.save_preferences(request.user, serializer.validated_data["preferences"])
        return Response(_success(CategorySerializer(categories, many=True).data, "Category preferences saved."))
