"""Deterministic routing and calibration utilities for System 1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RoutingDecision(str, Enum):
    """Possible destinations for an extracted policy."""

    AUTO_APPROVE = "auto_approve"
    SPOT_CHECK = "spot_check"
    HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class RoutingSignals:
    """Independent signals used to determine the routing decision."""

    confidence: float
    validation_passed: bool
    required_fields_present: bool
    disagreement_detected: bool = False


def route_record(signals: RoutingSignals) -> RoutingDecision:
    """Route one extracted policy using deterministic rules.

    Human review takes priority whenever an independent safeguard detects
    a potentially unreliable extraction.
    """

    if not signals.validation_passed:
        return RoutingDecision.HUMAN_REVIEW

    if not signals.required_fields_present:
        return RoutingDecision.HUMAN_REVIEW

    if signals.disagreement_detected:
        return RoutingDecision.HUMAN_REVIEW

    if signals.confidence < 0.80:
        return RoutingDecision.HUMAN_REVIEW

    if signals.confidence < 0.95:
        return RoutingDecision.SPOT_CHECK

    return RoutingDecision.AUTO_APPROVE


@dataclass(frozen=True)
class CalibrationLabel:
    """Observed correctness for one predicted extraction field."""

    policy_id: str
    policy_type: str
    field: str
    predicted_confidence: float
    correct: bool


@dataclass(frozen=True)
class CalibrationCell:
    """Calibration statistics for a policy-type and field slice."""

    samples: int
    mean_predicted_confidence: float
    observed_accuracy: float
    brier_score: float


@dataclass(frozen=True)
class CalibrationReport:
    """Complete sliced calibration report."""

    cells: dict[tuple[str, str], CalibrationCell]
    overall_brier: float


def _brier_score(labels: Iterable[CalibrationLabel]) -> float:
    items = list(labels)

    if not items:
        return 0.0

    total = 0.0

    for label in items:
        actual = 1.0 if label.correct else 0.0
        total += (label.predicted_confidence - actual) ** 2

    return total / len(items)


def calibration_report(
    labels: Iterable[CalibrationLabel],
) -> CalibrationReport:
    """Calculate calibration statistics sliced by policy type and field."""

    items = list(labels)

    grouped: dict[tuple[str, str], list[CalibrationLabel]] = {}

    for label in items:
        key = (label.policy_type, label.field)
        grouped.setdefault(key, []).append(label)

    cells: dict[tuple[str, str], CalibrationCell] = {}

    for key, group in grouped.items():
        samples = len(group)

        mean_confidence = sum(
            item.predicted_confidence for item in group
        ) / samples

        accuracy = sum(
            1 for item in group if item.correct
        ) / samples

        cells[key] = CalibrationCell(
            samples=samples,
            mean_predicted_confidence=mean_confidence,
            observed_accuracy=accuracy,
            brier_score=_brier_score(group),
        )

    return CalibrationReport(
        cells=cells,
        overall_brier=_brier_score(items),
    )
