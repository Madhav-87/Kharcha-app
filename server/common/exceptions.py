"""Common REST error envelope."""

from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, exceptions.ValidationError):
        code = "INVALID_REQUEST"
        detail = "Some submitted fields are invalid."
        fields = response.data if isinstance(response.data, dict) else {"non_field_errors": response.data}
    elif isinstance(exc, exceptions.AuthenticationFailed):
        code, detail, fields = "AUTHENTICATION_FAILED", "Authentication failed.", {}
    elif isinstance(exc, exceptions.NotAuthenticated):
        code, detail, fields = "NOT_AUTHENTICATED", "Authentication is required.", {}
    elif isinstance(exc, exceptions.PermissionDenied):
        code, detail, fields = "FORBIDDEN", "You do not have permission to perform this action.", {}
    elif isinstance(exc, exceptions.NotFound):
        code, detail, fields = "NOT_FOUND", "The requested resource was not found.", {}
    elif isinstance(exc, exceptions.Throttled):
        code, detail, fields = "RATE_LIMITED", "Too many requests. Try again later.", {}
    else:
        code = str(getattr(exc, "default_code", "request_failed")).upper()
        value = response.data.get("detail") if isinstance(response.data, dict) else None
        detail = str(value) if value else "The request could not be completed."
        fields = {}

    response.data = {
        "success": False,
        "error": {"code": code, "message": detail, "fields": fields},
    }
    return response
