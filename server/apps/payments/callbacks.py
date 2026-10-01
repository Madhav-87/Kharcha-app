"""Signature verification for trusted payment-provider callbacks."""

import hashlib
import hmac

from django.conf import settings
from rest_framework.exceptions import APIException, AuthenticationFailed


class CallbackIntegrationUnavailable(APIException):
    status_code = 503
    default_detail = "Verified UPI callbacks are not configured."
    default_code = "CALLBACK_UNAVAILABLE"


def verify_callback_signature(raw_body, signature):
    secret = getattr(settings, "UPI_CALLBACK_SECRET", "")
    if not secret:
        raise CallbackIntegrationUnavailable()
    if not signature:
        raise AuthenticationFailed("A callback signature is required.")
    supplied = signature.removeprefix("sha256=").strip().lower()
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, supplied):
        raise AuthenticationFailed("Callback signature is invalid.")
    return True
