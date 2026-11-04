"""Validation utilities for extracted insurance policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_FIELDS = (
    "policy_id",
    "policy_type",
    "holder_name",
    "premium_amount",
)


@dataclass(frozen=True)
class ValidationResult:
    """Result returned after validating an extracted policy."""

    valid: bool
    missing_fields: tuple[str, ...]
    errors: tuple[str, ...]


def validate_policy(data: dict[str, Any]) -> ValidationResult:
    """Validate required policy fields without fabricating missing values."""

    missing_fields = tuple(
        field
        for field in REQUIRED_FIELDS
        if data.get(field) is None or data.get(field) == ""
    )

    errors: list[str] = []

    if missing_fields:
        errors.append(
            "Missing required fields: " + ", ".join(missing_fields)
        )

    confidence = data.get("confidence")

    if confidence is not None:
        if not isinstance(confidence, (int, float)):
            errors.append("confidence must be numeric")
        elif not 0.0 <= float(confidence) <= 1.0:
            errors.append("confidence must be between 0 and 1")

    premium = data.get("premium_amount")

    if premium is not None:
        if not isinstance(premium, (int, float)):
            errors.append("premium_amount must be numeric")
        elif float(premium) < 0:
            errors.append("premium_amount cannot be negative")

    return ValidationResult(
        valid=not errors,
        missing_fields=missing_fields,
        errors=tuple(errors),
    )


def required_fields_present(data: dict[str, Any]) -> bool:
    """Return True only when every required field contains a value."""

    return all(
        data.get(field) is not None and data.get(field) != ""
        for field in REQUIRED_FIELDS
    )
