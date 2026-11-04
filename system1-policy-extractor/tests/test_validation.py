from policy_extractor.validation import (
    required_fields_present,
    validate_policy,
)


def test_valid_policy_passes_validation() -> None:
    policy = {
        "policy_id": "POL-001",
        "policy_type": "auto",
        "holder_name": "Sample Customer",
        "premium_amount": 1250.00,
        "confidence": 0.98,
    }

    result = validate_policy(policy)

    assert result.valid is True
    assert result.missing_fields == ()
    assert result.errors == ()


def test_missing_premium_is_reported() -> None:
    policy = {
        "policy_id": "POL-002",
        "policy_type": "home",
        "holder_name": "Sample Customer",
        "premium_amount": None,
        "confidence": 0.97,
    }

    result = validate_policy(policy)

    assert result.valid is False
    assert "premium_amount" in result.missing_fields


def test_missing_holder_name_is_reported() -> None:
    policy = {
        "policy_id": "POL-003",
        "policy_type": "umbrella",
        "holder_name": "",
        "premium_amount": 900.00,
        "confidence": 0.96,
    }

    result = validate_policy(policy)

    assert result.valid is False
    assert "holder_name" in result.missing_fields


def test_negative_premium_fails_validation() -> None:
    policy = {
        "policy_id": "POL-004",
        "policy_type": "auto",
        "holder_name": "Sample Customer",
        "premium_amount": -100.00,
        "confidence": 0.95,
    }

    result = validate_policy(policy)

    assert result.valid is False
    assert "premium_amount cannot be negative" in result.errors


def test_non_numeric_premium_fails_validation() -> None:
    policy = {
        "policy_id": "POL-005",
        "policy_type": "auto",
        "holder_name": "Sample Customer",
        "premium_amount": "unknown",
        "confidence": 0.95,
    }

    result = validate_policy(policy)

    assert result.valid is False
    assert "premium_amount must be numeric" in result.errors


def test_confidence_above_one_fails_validation() -> None:
    policy = {
        "policy_id": "POL-006",
        "policy_type": "auto",
        "holder_name": "Sample Customer",
        "premium_amount": 1000.00,
        "confidence": 1.50,
    }

    result = validate_policy(policy)

    assert result.valid is False
    assert "confidence must be between 0 and 1" in result.errors


def test_required_fields_present_returns_true() -> None:
    policy = {
        "policy_id": "POL-007",
        "policy_type": "home",
        "holder_name": "Sample Customer",
        "premium_amount": 1800.00,
    }

    assert required_fields_present(policy) is True


def test_required_fields_present_returns_false_for_null() -> None:
    policy = {
        "policy_id": "POL-008",
        "policy_type": "home",
        "holder_name": "Sample Customer",
        "premium_amount": None,
    }

    assert required_fields_present(policy) is False
