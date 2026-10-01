"""Unit checks for audit metadata redaction."""

from django.test import SimpleTestCase

from apps.audit.services import _safe_metadata


class SafeAuditMetadataTests(SimpleTestCase):
    def test_removes_sensitive_keys_recursively(self):
        metadata = {
            "event": "login",
            "refresh_token": "raw-token",
            "nested": {"api_key": "secret", "count": 2},
        }

        self.assertEqual(
            _safe_metadata(metadata),
            {"event": "login", "nested": {"count": 2}},
        )

    def test_sanitizes_keys_in_lists(self):
        self.assertEqual(
            _safe_metadata([{"password_hash": "hash", "status": "ok"}]),
            [{"status": "ok"}],
        )
