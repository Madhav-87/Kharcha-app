"""Transactional category and preference operations."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import NotFound, ValidationError

from apps.categories.models import Category, UserCategory


def get_category_for_user(user, public_id, *, include_archived=False):
    categories = Category.objects.filter(public_id=public_id).filter(
        models_user_scope(user)
    )
    if not include_archived:
        categories = categories.filter(archived_at__isnull=True)
    category = categories.first()
    if category is None:
        raise NotFound("Category was not found.")
    return category


def models_user_scope(user):
    from django.db.models import Q

    return Q(user__isnull=True) | Q(user=user)


def _category_slug(user, name, *, exclude_id=None):
    base = slugify(name)[:80].strip("-")
    if not base:
        raise ValidationError({"name": "Enter a name containing letters or numbers."})
    slug = base
    suffix = 2
    qs = Category.objects.filter(user=user)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    while qs.filter(slug=slug).exists():
        ending = f"-{suffix}"
        slug = f"{base[:80-len(ending)]}{ending}"
        suffix += 1
    return slug


@transaction.atomic
def create_category(user, values):
    name = values["name"].strip()
    if Category.objects.filter(user=user, name__iexact=name).exists():
        raise ValidationError({"name": "You already have a category with this name."})
    category = Category.objects.create(
        user=user,
        name=name,
        slug=_category_slug(user, name),
        icon=values["icon"],
        emoji=values.get("emoji"),
        color=values["color"],
        is_default=False,
        sort_order=values.get("sort_order", 0),
    )
    category.user_category_preference = UserCategory.objects.create(user=user, category=category)
    return category


@transaction.atomic
def update_category(user, category, values):
    if category.user_id != user.pk:
        raise ValidationError("System categories cannot be edited.")
    if "name" in values:
        name = values["name"].strip()
        if Category.objects.filter(user=user, name__iexact=name).exclude(pk=category.pk).exists():
            raise ValidationError({"name": "You already have a category with this name."})
        category.name = name
        category.slug = _category_slug(user, name, exclude_id=category.pk)
    for field in ("icon", "emoji", "color", "sort_order"):
        if field in values:
            setattr(category, field, values[field])
    try:
        category.save(update_fields=("name", "slug", "icon", "emoji", "color", "sort_order"))
    except IntegrityError as exc:
        raise ValidationError({"name": "A category with these details already exists."}) from exc
    return category


@transaction.atomic
def archive_category(user, category):
    if category.user_id != user.pk:
        raise ValidationError("System categories cannot be deleted.")
    category.archived_at = timezone.now()
    category.save(update_fields=("archived_at",))


@transaction.atomic
def save_preferences(user, values):
    results = []
    for item in values:
        category = get_category_for_user(user, item["category_public_id"])
        preference = UserCategory.objects.filter(user=user, category=category).first()
        if preference is None:
            preference = UserCategory(user=user, category=category)
        is_new = preference._state.adding
        for field, model_field in (
            ("hidden", "hidden"),
            ("color_override", "color_override"),
            ("icon_override", "icon_override"),
            ("sort_order", "sort_order"),
        ):
            if field in item:
                setattr(preference, model_field, item[field])
        if is_new:
            try:
                with transaction.atomic():
                    preference.save()
            except IntegrityError:
                # Concurrent preference creation: apply values to the row that won.
                preference = UserCategory.objects.get(user=user, category=category)
                for field in ("hidden", "color_override", "icon_override", "sort_order"):
                    if field in item:
                        setattr(preference, field, item[field])
                preference.save()
        else:
            preference.save()
        category.user_category_preference = preference
        results.append(category)
    return results
