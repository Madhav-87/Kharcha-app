"""FCM HTTP v1 sender using the configured Google service account."""

import json
import urllib.error
import urllib.request

from django.conf import settings


FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


class FCMDeliveryError(Exception):
    def __init__(self, code, message, *, retryable=False, token_invalid=False):
        super().__init__(message)
        self.code = str(code)[:80]
        self.retryable = retryable
        self.token_invalid = token_invalid


def _access_token():
    service_account_file = getattr(settings, "FCM_SERVICE_ACCOUNT_FILE", "")
    project_id = getattr(settings, "FCM_PROJECT_ID", "")
    if not service_account_file or not project_id:
        raise FCMDeliveryError("fcm_not_configured", "FCM project or service account file is not configured.")
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=[FCM_SCOPE]
        )
        credentials.refresh(Request())
    except Exception as exc:
        raise FCMDeliveryError(
            "fcm_credentials_error", "Could not obtain FCM credentials.", retryable=True
        ) from exc
    return project_id, credentials.token


def _string_data(notification):
    data = {"notification_public_id": str(notification.public_id), "type": notification.type}
    if notification.deep_link:
        data["deep_link"] = notification.deep_link
    for key, value in (notification.data or {}).items():
        if isinstance(value, (dict, list)):
            data[str(key)] = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        elif value is None:
            data[str(key)] = ""
        else:
            data[str(key)] = str(value)
    return data


def send_notification(device, notification):
    project_id, access_token = _access_token()
    endpoint = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    message = {
        "message": {
            "token": device.fcm_token,
            "notification": {"title": notification.title, "body": notification.body or ""},
            "data": _string_data(notification),
        }
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(message, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("name", "")
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            details = payload.get("error", {})
            code = details.get("status") or exc.code
            message = details.get("message") or "FCM rejected the message."
            error_details = details.get("details", [])
            detail_codes = {entry.get("errorCode") for entry in error_details if isinstance(entry, dict)}
        except (ValueError, UnicodeDecodeError):
            code, message, detail_codes = exc.code, "FCM rejected the message.", set()
        token_invalid = code == "UNREGISTERED" or "UNREGISTERED" in detail_codes
        retryable = exc.code >= 500 or exc.code == 429 or code in {"UNAVAILABLE", "INTERNAL", "RESOURCE_EXHAUSTED"}
        raise FCMDeliveryError(code, message, retryable=retryable, token_invalid=token_invalid) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise FCMDeliveryError("network_error", "FCM could not be reached.", retryable=True) from exc
