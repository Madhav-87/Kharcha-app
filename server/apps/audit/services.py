"""Create sanitized, append-only audit events."""

from apps.audit.models import AuditLog


_SENSITIVE_KEY_PARTS = (
    "password", "secret", "token", "authorization", "credential", "key"
)


def _safe_metadata(value):
    if isinstance(value, dict):
        return {
            key: _safe_metadata(item)
            for key, item in value.items()
            if not any(part in str(key).lower().replace("_", "") for part in _SENSITIVE_KEY_PARTS)
        }
    if isinstance(value, (list, tuple)):
        return [_safe_metadata(item) for item in value]
    return value


def record_event(
    user,
    action,
    *,
    entity_type=None,
    entity_id=None,
    ip_address=None,
    metadata=None,
):
    """Persist an event while filtering metadata keys that can contain secrets."""
    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        metadata=_safe_metadata(metadata) or None,
    )
