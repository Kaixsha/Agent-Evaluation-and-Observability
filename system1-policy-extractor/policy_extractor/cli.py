"""Command-line interface for the policy extraction pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policy_extractor.pipeline import (
    PipelineResult,
    process_batch,
    routing_counts,
)


def replay_extract(source: str, attempt: int) -> dict[str, Any]:
    """Load deterministic extraction data from a JSON policy fixture."""

    path = Path(source)

    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    # Optional fixture behavior used to demonstrate validation-driven retry.
    if data.get("retry_demo") and attempt == 1:
        data = dict(data)
        data["premium_amount"] = None

    return data


def find_documents(directory: Path) -> list"""Return policy fixture files in deterministic order."""

    return [
        str(path)
        for path in sorted(directory.glob("*.json"))
    ]


def write_routing_output(
    results: list[PipelineResult],
    output_path: Path,
) -> None:
    """Write observable routing decisions to JSON."""

    payload = [result.to_dict() for result in results]

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def run_pipeline(
    data_directory: Path,
    routing_output: Path,
) -> int:
    """Execute the deterministic batch pipeline."""

    sources = find_documents(data_directory)

    if not sources:
        print(f"No JSON policy documents found in {data_directory}")
        return 1

    results = process_batch(
        sources,
        replay_extract,
        max_attempts=2,
    )

    write_routing_output(results, routing_output)

    print("POLICY EXTRACTION PIPELINE")
    print("=" * 50)

    for result in results:
        print(f"source: {result.source}")
        print(f"attempts: {result.extraction_attempts}")
        print(f"validation_passed: {result.validation.valid}")
        print(f"routing: {result.routing_decision.value}")
        print(f"signal: {result.routing_signal}")
        print("-" * 50)

    counts = routing_counts(results)

    print("ROUTING COUNTS")
    print(f"auto_approve: {counts['auto_approve']}")
    print(f"human_review: {counts['human_review']}")
    print(f"spot_check: {counts['spot_check']}")
    print()
    print(f"Routing decisions written to: {routing_output}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="policy-extractor",
        description="Validated insurance policy extraction pipeline.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Process a directory of policy documents.",
    )

    pipeline_parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing JSON policy fixtures.",
    )

    pipeline_parser.add_argument(
        "--routing-out",
        type=Path,
        default=Path("routing_decisions.json"),
        help="Output file for routing decisions.",
    )

    pipeline_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic seed retained for interface compatibility.",
    )

    return parser


def main() -> int:
    """Run the policy-extractor command."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "pipeline":
        # Seed is intentionally accepted to make repeated runs explicit
        # and reproducible. Current routing itself is deterministic.
        _ = args.seed

        return run_pipeline(
            args.directory,
            args.routing_out,
        )

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
