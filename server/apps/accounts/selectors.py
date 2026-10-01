"""Account read/query helpers, always scoped to the authenticated user."""

from apps.accounts.models import AuthSession, User, UserSettings
from apps.categories.models import UserCategory


def get_user_by_public_id(public_id: str) -> User | None:
    return User.objects.filter(public_id=public_id).first()


def get_user_settings(user: User) -> UserSettings:
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    return settings_obj


def get_user_sessions(user: User):
    return AuthSession.objects.filter(user=user).order_by("-last_active_at")


def get_onboarding_category_ids(user: User) -> list[str]:
    return list(
        UserCategory.objects.filter(user=user)
        .select_related("category")
        .order_by("sort_order")
        .values_list("category__public_id", flat=True)
    )
