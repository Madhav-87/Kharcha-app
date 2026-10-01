from django.urls import path

from apps.categories.views import (
    CategoryDetailView,
    CategoryListCreateView,
    CategoryPreferencesView,
)

urlpatterns = [
    path("", CategoryListCreateView.as_view(), name="category-list-create"),
    path("preferences/", CategoryPreferencesView.as_view(), name="category-preferences"),
    path("<uuid:public_id>/", CategoryDetailView.as_view(), name="category-detail"),
]
