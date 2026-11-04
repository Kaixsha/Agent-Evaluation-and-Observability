"""Targeted perturbation tests for validation-driven retry."""

from typing import Any

from policy_extractor.pipeline import process_document
from policy_extractor.routing import RoutingDecision


def test_null_required_field_triggers_retry_then_recovers() -> None:
    calls: list[int] = []

    def extract(source: str, attempt: int) -> dict[str, Any]:
        calls.append(attempt)

        if attempt == 1:
            return {
                "policy_id": "POL-PERTURB-01",
                "policy_type": "auto",
                "holder_name": "Test Customer",
                "premium_amount": None,
                "confidence": 0.98,
            }

        return {
            "policy_id": "POL-PERTURB-01",
            "policy_type": "auto",
            "holder_name": "Test Customer",
            "premium_amount": 1500.00,
            "confidence": 0.98,
        }

    result = process_document(
        "perturbed-policy",
        extract,
        max_attempts=2,
    )

    assert calls == [1, 2]
    assert result.extraction_attempts == 2
    assert result.validation.valid is True
    assert result.routing_decision == RoutingDecision.AUTO_APPROVE


def test_null_required_field_stays_invalid_and_escalates() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": "POL-PERTURB-02",
            "policy_type": "home",
            "holder_name": "Test Customer",
            "premium_amount": None,
            "confidence": 0.99,
        }

    result = process_document(
        "persistently-invalid-policy",
        extract,
        max_attempts=2,
    )

    assert result.extraction_attempts == 2
    assert result.validation.valid is False
    assert "premium_amount" in result.validation.missing_fields
    assert result.routing_decision == RoutingDecision.HUMAN_REVIEW
    assert result.routing_signal == "schema_validation_failed"
