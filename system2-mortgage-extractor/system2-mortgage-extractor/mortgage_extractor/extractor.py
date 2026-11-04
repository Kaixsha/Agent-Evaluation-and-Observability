"""Schema-enforced two-pass extraction for mortgage documents."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum


class DocumentType(str, Enum):
    """Mortgage document types supported by the extractor."""

    APPRAISAL = "appraisal"
    INCOME_STATEMENT = "income_statement"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ExtractionResult:
    """Structured extraction result."""

    document_type: DocumentType
    square_feet: int | None = None
    base_salary: float | None = None
    overtime: float | None = None
    bonus: float | None = None
    stated_total: float | None = None


@dataclass(frozen=True)
class ConsistencyResult:
    """Arithmetic-consistency validation result."""

    consistent: bool
    calculated_total: float | None
    stated_total: float | None
    discrepancy: float | None
    message: str


def classify_document(text: str) -> DocumentType:
    """Classify a document before structured extraction."""

    normalized = text.lower()

    appraisal_terms = ("appraisal", "property", "square feet", "sq ft")
    income_terms = ("income", "salary", "overtime", "bonus", "total")

    if any(term in normalized for term in appraisal_terms):
        if "sq ft" in normalized or "square feet" in normalized:
            return DocumentType.APPRAISAL

    if any(term in normalized for term in income_terms):
        return DocumentType.INCOME_STATEMENT

    return DocumentType.UNKNOWN


def _parse_number(value: str) -> float:
    """Convert a formatted numeric string to a float."""

    return float(value.replace(",", "").replace("$", "").strip())


def _extract_money(text: str, label: str) -> float | None:
    """Extract a monetary value following a field label."""

    pattern = rf"{re.escape(label)}\s*:\s*\$?([\d,]+(?:\.\d+)?)"
    match = re.search(pattern, text, flags=re.IGNORECASE)

    if match is None:
        return None

    return _parse_number(match.group(1))


def _extract_square_feet(text: str) -> int | None:
    """Normalize informal square-foot measurements to an integer."""

    pattern = r"(?:about\s+)?([\d,]+)\s*(?:sq\s*ft|square\s*feet)"
    match = re.search(pattern, text, flags=re.IGNORECASE)

    if match is None:
        return None

    return int(match.group(1).replace(",", ""))


def first_pass_extract(
    text: str,
    document_type: DocumentType,
) -> ExtractionResult:
    """Perform the first structured extraction pass."""

    if document_type == DocumentType.APPRAISAL:
        return ExtractionResult(
            document_type=document_type,
            square_feet=_extract_square_feet(text),
        )

    if document_type == DocumentType.INCOME_STATEMENT:
        return ExtractionResult(
            document_type=document_type,
            base_salary=_extract_money(text, "Base salary"),
            overtime=_extract_money(text, "Overtime"),
            bonus=_extract_money(text, "Bonus"),
            stated_total=_extract_money(text, "Stated total"),
        )

    return ExtractionResult(document_type=DocumentType.UNKNOWN)


def second_pass_enforce_schema(
    result: ExtractionResult,
) -> ExtractionResult:
    """Enforce the schema without fabricating unavailable values."""

    if result.document_type == DocumentType.APPRAISAL:
        return ExtractionResult(
            document_type=result.document_type,
            square_feet=result.square_feet,
        )

    if result.document_type == DocumentType.INCOME_STATEMENT:
        return ExtractionResult(
            document_type=result.document_type,
            base_salary=result.base_salary,
            overtime=result.overtime,
            bonus=result.bonus,
            stated_total=result.stated_total,
        )

    return ExtractionResult(document_type=DocumentType.UNKNOWN)


def extract_document(text: str) -> ExtractionResult:
    """Classify and extract a document using two deterministic passes."""

    document_type = classify_document(text)
    first_pass = first_pass_extract(text, document_type)
    return second_pass_enforce_schema(first_pass)


def validate_consistency(
    result: ExtractionResult,
) -> ConsistencyResult:
    """Compare income line items with the document's stated total."""

    if result.document_type != DocumentType.INCOME_STATEMENT:
        return ConsistencyResult(
            consistent=True,
            calculated_total=None,
            stated_total=None,
            discrepancy=None,
            message="Arithmetic consistency check is not applicable.",
        )

    line_items = (
        result.base_salary,
        result.overtime,
        result.bonus,
    )

    available_values = [
        value for value in line_items if value is not None
    ]

    if result.stated_total is None:
        return ConsistencyResult(
            consistent=False,
            calculated_total=sum(available_values),
            stated_total=None,
            discrepancy=None,
            message="Consistency check incomplete: stated total is missing.",
        )

    calculated_total = sum(available_values)
    discrepancy = result.stated_total - calculated_total
    consistent = abs(discrepancy) < 0.01

    if consistent:
        message = "Consistency check passed: line-item sum matches stated total."
    else:
        message = (
            "Consistency discrepancy: "
            f"line-item sum={calculated_total:.2f}, "
            f"stated total={result.stated_total:.2f}, "
            f"difference={discrepancy:.2f}."
        )

    return ConsistencyResult(
        consistent=consistent,
        calculated_total=calculated_total,
        stated_total=result.stated_total,
        discrepancy=discrepancy,
        message=message,
    )


def result_to_dict(result: ExtractionResult) -> dict[str, object]:
    """Convert an extraction result to a serializable dictionary."""

    data = asdict(result)
    data["document_type"] = result.document_type.value
    return data
