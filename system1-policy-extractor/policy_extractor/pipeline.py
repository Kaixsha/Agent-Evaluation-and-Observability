"""Validated, retried, batch-processing policy extraction pipeline."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from typing import Any

from policy_extractor.routing import (
    RoutingDecision,
    RoutingSignals,
    route_record,
)
from policy_extractor.validation import (
    ValidationResult,
    required_fields_present,
    validate_policy,
)

ExtractFunction = Callable[[str, int], dict[str, Any]]


@dataclass(frozen=True)
class PipelineResult:
    """Final observable result for one policy document."""

    source: str
    extracted_data: dict[str, Any]
    validation: ValidationResult
    routing_decision: RoutingDecision
    routing_signal: str
    extraction_attempts: int

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a JSON-serializable dictionary."""
        result = asdict(self)
        result["routing_decision"] = self.routing_decision.value
        return result


def identify_routing_signal(
    validation: ValidationResult,
    confidence: float,
    disagreement_detected: bool,
) -> str:
    """Name the independent signal that determined routing."""

    if not validation.valid:
        return "schema_validation_failed"

    if validation.missing_fields:
        return "required_field_missing"

    if disagreement_detected:
        return "independent_extractor_disagreement"

    if confidence < 0.80:
        return "confidence_below_0.80"

    if confidence < 0.95:
        return "confidence_below_0.95"

    return "all_safeguards_passed"


def process_document(
    source: str,
    extract: ExtractFunction,
    *,
    max_attempts: int = 2,
) -> PipelineResult:
    """Extract, validate, retry when needed, and route a document."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    extracted_data: dict[str, Any] = {}
    validation = validate_policy(extracted_data)
    attempts = 0

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        extracted_data = extract(source, attempt)
        validation = validate_policy(extracted_data)

        if validation.valid:
            break

    confidence_value = extracted_data.get("confidence", 0.0)

    confidence = (
        float(confidence_value)
        if isinstance(confidence_value, (int, float))
        else 0.0
    )

    disagreement_detected = bool(
        extracted_data.get("disagreement_detected", False)
    )

    signals = RoutingSignals(
        confidence=confidence,
        validation_passed=validation.valid,
        required_fields_present=required_fields_present(extracted_data),
        disagreement_detected=disagreement_detected,
    )

    routing_decision = route_record(signals)

    routing_signal = identify_routing_signal(
        validation=validation,
        confidence=confidence,
        disagreement_detected=disagreement_detected,
    )

    return PipelineResult(
        source=source,
        extracted_data=extracted_data,
        validation=validation,
        routing_decision=routing_decision,
        routing_signal=routing_signal,
        extraction_attempts=attempts,
    )


def process_batch(
    sources: Iterable[str],
    extract: ExtractFunction,
    *,
    max_attempts: int = 2,
) -> list[PipelineResult]:
    """Process several documents while preserving source order."""

    return [
        process_document(
            source,
            extract,
            max_attempts=max_attempts,
        )
        for source in sources
    ]   


def routing_counts(
    results: Iterable[PipelineResult],
) -> dict[str, int]:
    """Count each deterministic routing outcome."""

    counts = {
        RoutingDecision.AUTO_APPROVE.value: 0,
        RoutingDecision.HUMAN_REVIEW.value: 0,
        RoutingDecision.SPOT_CHECK.value: 0,
    }

    for result in results:
        counts[result.routing_decision.value] += 1

    return counts