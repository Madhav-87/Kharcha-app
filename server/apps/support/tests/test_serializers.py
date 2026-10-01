"""Validation checks for support and privacy inputs."""

from django.test import SimpleTestCase

from apps.support.serializers import DeleteAccountSerializer, IssueReportCreateSerializer


class IssueReportValidationTests(SimpleTestCase):
    def test_issue_cannot_link_both_expense_and_payment(self):
        serializer = IssueReportCreateSerializer(
            data={
                "subject": "Payment issue",
                "expense_public_id": "e9971ec1-e2c7-4494-91d2-46d1623c7b7b",
                "payment_public_id": "77b98b03-3d78-4be2-a6b8-8039813175f4",
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_general_issue_needs_only_a_subject(self):
        serializer = IssueReportCreateSerializer(data={"subject": "Account question"})

        self.assertTrue(serializer.is_valid(), serializer.errors)


class DeleteAccountValidationTests(SimpleTestCase):
    def test_deletion_requires_explicit_confirmation(self):
        serializer = DeleteAccountSerializer(data={"confirm": False})

        self.assertFalse(serializer.is_valid())

    def test_confirmed_deletion_is_valid(self):
        serializer = DeleteAccountSerializer(data={"confirm": True})

        self.assertTrue(serializer.is_valid(), serializer.errors)
