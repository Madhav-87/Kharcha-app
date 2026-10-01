"""Account access policies."""

from rest_framework.permissions import BasePermission


class IsActiveAccount(BasePermission):
    """Require a signed-in account that has not been suspended or deleted."""

    message = "This account is not active."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)
