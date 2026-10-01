"""Read queries for categories and user-specific display preferences."""

from django.db.models import Q

from apps.categories.models import Category, UserCategory


def list_categories(user, *, include_hidden=True):
    categories = list(
        Category.objects.filter(Q(user__isnull=True) | Q(user=user), archived_at__isnull=True)
    )
    preferences = {
        preference.category_id: preference
        for preference in UserCategory.objects.filter(user=user, category__in=categories)
    }
    for category in categories:
        category.user_category_preference = preferences.get(category.pk)
    if not include_hidden:
        categories = [
            category for category in categories
            if not getattr(category.user_category_preference, "hidden", False)
        ]
    categories.sort(
        key=lambda category: (
            category.sort_order if category.user_id is not None else getattr(
                category.user_category_preference, "sort_order", category.sort_order
            ),
            category.name.casefold(),
        )
    )
    return categories
