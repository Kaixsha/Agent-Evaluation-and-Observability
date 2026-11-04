from policy_extractor.routing import (
    CalibrationLabel,
    RoutingDecision,
    RoutingSignals,
    calibration_report,
    route_record,
)


def test_auto_approve_high_confidence_valid_record() -> None:
    signals = RoutingSignals(
        confidence=0.98,
        validation_passed=True,
        required_fields_present=True,
    )

    assert route_record(signals) == RoutingDecision.AUTO_APPROVE


def test_spot_check_medium_confidence_record() -> None:
    signals = RoutingSignals(
        confidence=0.90,
        validation_passed=True,
        required_fields_present=True,
    )

    assert route_record(signals) == RoutingDecision.SPOT_CHECK


def test_human_review_low_confidence_record() -> None:
    signals = RoutingSignals(
        confidence=0.70,
        validation_passed=True,
        required_fields_present=True,
    )

    assert route_record(signals) == RoutingDecision.HUMAN_REVIEW


def test_human_review_when_validation_fails() -> None:
    signals = RoutingSignals(
        confidence=0.99,
        validation_passed=False,
        required_fields_present=True,
    )

    assert route_record(signals) == RoutingDecision.HUMAN_REVIEW


def test_human_review_when_required_field_missing() -> None:
    signals = RoutingSignals(
        confidence=0.99,
        validation_passed=True,
        required_fields_present=False,
    )

    assert route_record(signals) == RoutingDecision.HUMAN_REVIEW


def test_human_review_when_independent_extractors_disagree() -> None:
    signals = RoutingSignals(
        confidence=0.99,
        validation_passed=True,
        required_fields_present=True,
        disagreement_detected=True,
    )

    assert route_record(signals) == RoutingDecision.HUMAN_REVIEW


def test_calibration_report_exposes_bad_slice() -> None:
    labels = [
        CalibrationLabel(
            policy_id="POL-1",
            policy_type="auto",
            field="premium_amount",
            predicted_confidence=0.95,
            correct=True,
        ),
        CalibrationLabel(
            policy_id="POL-2",
            policy_type="auto",
            field="premium_amount",
            predicted_confidence=0.95,
            correct=True,
        ),
        CalibrationLabel(
            policy_id="POL-3",
            policy_type="auto",
            field="premium_amount",
            predicted_confidence=0.95,
            correct=True,
        ),
        CalibrationLabel(
            policy_id="POL-4",
            policy_type="umbrella",
            field="exclusions",
            predicted_confidence=0.93,
            correct=False,
        ),
        CalibrationLabel(
            policy_id="POL-5",
            policy_type="umbrella",
            field="exclusions",
            predicted_confidence=0.93,
            correct=False,
        ),
        CalibrationLabel(
            policy_id="POL-6",
            policy_type="home",
            field="deductible",
            predicted_confidence=0.90,
            correct=True,
        ),
    ]

    report = calibration_report(labels)

    bad_cell = report.cells[("umbrella", "exclusions")]

    assert bad_cell.samples == 2
    assert bad_cell.mean_predicted_confidence == 0.93
    assert bad_cell.observed_accuracy == 0.0
