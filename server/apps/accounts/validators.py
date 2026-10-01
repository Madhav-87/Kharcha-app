"""Reusable account input validators."""

from django.core.validators import RegexValidator


validate_indian_phone = RegexValidator(
    regex=r"^\+91[6-9][0-9]{9}$",
    message="Enter an Indian mobile number in +91XXXXXXXXXX format.",
    code="invalid_phone",
)
