from typing import Any

from policy_extractor.pipeline import (
    process_batch,
    process_document,
    routing_counts,
)
from policy_extractor.routing import RoutingDecision


def test_invalid_first_attempt_retries_and_succeeds() -> None:
    calls: list[int] = []

    def extract(source: str, attempt: int) -> dict[str, Any]:
        calls.append(attempt)

        if attempt == 1:
            return {
                "policy_id": "POL-101",
                "policy_type": "auto",
                "holder_name": "Sample Customer",
                "premium_amount": None,
                "confidence": 0.98,
            }

        return {
            "policy_id": "POL-101",
            "policy_type": "auto",
            "holder_name": "Sample Customer",
            "premium_amount": 1200.00,
            "confidence": 0.98,
        }

    result = process_document("policy-101", extract)

    assert calls == [1, 2]
    assert result.extraction_attempts == 2
    assert result.validation.valid is True
    assert result.routing_decision == RoutingDecision.AUTO_APPROVE


def test_persistent_null_required_field_routes_to_human_review() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": "POL-102",
            "policy_type": "home",
            "holder_name": "Sample Customer",
            "premium_amount": None,
            "confidence": 0.99,
        }

    result = process_document("policy-102", extract)

    assert result.extraction_attempts == 2
    assert result.validation.valid is False
    assert result.routing_decision == RoutingDecision.HUMAN_REVIEW
    assert result.routing_signal == "schema_validation_failed"


def test_low_confidence_is_independent_human_review_signal() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": "POL-103",
            "policy_type": "umbrella",
            "holder_name": "Sample Customer",
            "premium_amount": 850.00,
            "confidence": 0.72,
        }

    result = process_document("policy-103", extract)

    assert result.validation.valid is True
    assert result.routing_decision == RoutingDecision.HUMAN_REVIEW
    assert result.routing_signal == "confidence_below_0.80"


def test_disagreement_is_independent_human_review_signal() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": "POL-104",
            "policy_type": "auto",
            "holder_name": "Sample Customer",
            "premium_amount": 1400.00,
            "confidence": 0.99,
            "disagreement_detected": True,
        }

    result = process_document("policy-104", extract)

    assert result.validation.valid is True
    assert result.routing_decision == RoutingDecision.HUMAN_REVIEW
    assert result.routing_signal == "independent_extractor_disagreement"


def test_medium_confidence_routes_to_spot_check() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": "POL-105",
            "policy_type": "home",
            "holder_name": "Sample Customer",
            "premium_amount": 1600.00,
            "confidence": 0.90,
        }

    result = process_document("policy-105", extract)

    assert result.routing_decision == RoutingDecision.SPOT_CHECK
    assert result.routing_signal == "confidence_below_0.95"


def test_high_confidence_routes_to_auto_approve() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": "POL-106",
            "policy_type": "auto",
            "holder_name": "Sample Customer",
            "premium_amount": 1100.00,
            "confidence": 0.98,
        }

    result = process_document("policy-106", extract)

    assert result.routing_decision == RoutingDecision.AUTO_APPROVE
    assert result.routing_signal == "all_safeguards_passed"


def test_batch_processing_preserves_source_order() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        return {
            "policy_id": source,
            "policy_type": "auto",
            "holder_name": "Sample Customer",
            "premium_amount": 1000.00,
            "confidence": 0.98,
        }

    results = process_batch(
        ["POL-A", "POL-B", "POL-C"],
        extract,
    )

    assert [result.source for result in results] == [
        "POL-A",
        "POL-B",
        "POL-C",
    ]


def test_routing_counts_include_all_three_routes() -> None:
    def extract(source: str, attempt: int) -> dict[str, Any]:
        confidence_by_source = {
            "approve": 0.98,
            "spot": 0.90,
            "review": 0.70,
        }

        return {
            "policy_id": source,
            "policy_type": "auto",
            "holder_name": "Sample Customer",
            "premium_amount": 1000.00,
            "confidence": confidence_by_source[source],
        }

    results = process_batch(
        ["approve", "spot", "review"],
        extract,
    )

    counts = routing_counts(results)

    assert counts["auto_approve"] == 1
    assert counts["spot_check"] == 1
    assert counts["human_review"] == 1
