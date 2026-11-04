"""Command-line interface for mortgage extraction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mortgage_extractor.extractor import (
    extract_document,
    result_to_dict,
    validate_consistency,
)


def run_extraction(document: Path, mode: str) -> int:
    """Run deterministic extraction against one document."""

    if not document.exists():
        print(f"Document not found: {document}")
        return 1

    text = document.read_text(encoding="utf-8")

    result = extract_document(text)
    consistency = validate_consistency(result)

    print("MORTGAGE DOCUMENT EXTRACTION")
    print("=" * 50)
    print(f"document: {document}")
    print(f"mode: {mode}")
    print(f"document_type: {result.document_type.value}")
    print()
    print("STRUCTURED EXTRACTION")
    print(json.dumps(result_to_dict(result), indent=2))
    print()
    print("CONSISTENCY VALIDATION")
    print(consistency.message)

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        prog="mortgage-extract",
        description="Schema-enforced mortgage document extractor.",
    )

    parser.add_argument(
        "document",
        type=Path,
        help="Mortgage document to extract.",
    )

    parser.add_argument(
        "--mode",
        choices=("replay", "record"),
        default="replay",
        help="Extraction mode.",
    )

    return parser


def main() -> int:
    """Run the command-line application."""

    args = build_parser().parse_args()
    return run_extraction(args.document, args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
