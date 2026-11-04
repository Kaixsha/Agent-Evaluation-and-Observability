"""Tests for schema-enforced mortgage extraction."""

from mortgage_extractor.extractor import (
    DocumentType,
    extract_document,
    validate_consistency,
)


def test_appraisal_classification_and_sqft_normalization() -> None:
    text = """
    PROPERTY APPRAISAL
    Property type: Single-family residence
    Living area: about 2,400 sq ft
    """

    result = extract_document(text)

    assert result.document_type == DocumentType.APPRAISAL
    assert result.square_feet == 2400


def test_missing_bonus_returns_none() -> None:
    text = """
    INCOME STATEMENT
    Base salary: $60000
    Overtime: $5000
    Stated total: $65000
    """

    result = extract_document(text)

    assert result.document_type == DocumentType.INCOME_STATEMENT
    assert result.base_salary == 60000.0
    assert result.overtime == 5000.0
    assert result.bonus is None
    assert result.stated_total == 65000.0


def test_consistency_validator_detects_sum_mismatch() -> None:
    text = """
    INCOME STATEMENT
    Base salary: $60000
    Overtime: $5000
    Bonus: $5000
    Stated total: $75000
    """

    result = extract_document(text)
    consistency = validate_consistency(result)

    assert consistency.consistent is False
    assert consistency.calculated_total == 70000.0
    assert consistency.stated_total == 75000.0
    assert consistency.discrepancy == 5000.0
    assert "Consistency discrepancy" in consistency.message


def test_matching_income_total_passes_consistency() -> None:
    text = """
    INCOME STATEMENT
    Base salary: $60000
    Overtime: $5000
    Bonus: $5000
    Stated total: $70000
    """

    result = extract_document(text)
    consistency = validate_consistency(result)

    assert consistency.consistent is True
    assert consistency.discrepancy == 0.0


def test_unknown_document_does_not_invent_values() -> None:
    text = "This document contains no recognized mortgage fields."

    result = extract_document(text)

    assert result.document_type == DocumentType.UNKNOWN
    assert result.square_feet is None
    assert result.base_salary is None
    assert result.overtime is None
    assert result.bonus is None
    assert result.stated_total is None
