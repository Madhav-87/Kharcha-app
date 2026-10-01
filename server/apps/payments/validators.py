"""Validation shared by payment and saved-payee APIs."""

import re

from rest_framework import serializers


UPI_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{2,64}@[A-Za-z]{2,32}$")


def validate_upi_id(value):
    value = value.strip()
    if not UPI_ID_PATTERN.fullmatch(value):
        raise serializers.ValidationError("Enter a valid UPI ID.")
    return value
