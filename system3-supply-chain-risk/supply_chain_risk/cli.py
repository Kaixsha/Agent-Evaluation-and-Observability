"""Command-line interface for supply-chain investigations."""

from __future__ import annotations

import argparse
from pathlib import Path

from supply_chain_risk.investigation import (
    build_findings,
    meridian_sources,
    render_briefing,
)


def run_investigation(
    company: str,
    *,
    offline: bool,
    simulate_timeout: bool,
) -> int:
    """Run an offline deterministic investigation."""

    if company.lower() != "meridian":
        print(f"Unknown investigation target: {company}")
        return 1

    if not offline:
        print("This reference implementation currently supports --offline mode.")
        return 1

    claims = meridian_sources(simulate_timeout=simulate_timeout)
    findings = build_findings(claims)
    briefing = render_briefing(findings)

    output_path = Path("meridian_briefing.md")
    output_path.write_text(briefing + "\n", encoding="utf-8")

    print("SUPPLY-CHAIN RISK INVESTIGATION")
    print("=" * 50)
    print(f"target: {company}")
    print(f"offline: {offline}")
    print(f"simulate_timeout: {simulate_timeout}")
    print()
    print(briefing)
    print()
    print(f"Briefing written to: {output_path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""

    parser = argparse.ArgumentParser(
        prog="supply-chain-investigate",
        description="Provenance-preserving supply-chain investigation.",
    )

    parser.add_argument(
        "company",
        help="Company to investigate.",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use deterministic offline source fixtures.",
    )

    parser.add_argument(
        "--simulate-timeout",
        action="store_true",
        help="Simulate failure of one evidence source.",
    )

    return parser


def main() -> int:
    """Run the command-line application."""

    args = build_parser().parse_args()

    return run_investigation(
        args.company,
        offline=args.offline,
        simulate_timeout=args.simulate_timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
