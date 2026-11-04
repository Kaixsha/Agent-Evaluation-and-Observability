"""Provenance-preserving multi-source supply-chain investigation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FindingStatus(str, Enum):
    """Classification used in the final investigation briefing."""

    WELL_ESTABLISHED = "Well-Established"
    CONTESTED = "Contested"
    INCOMPLETE = "Incomplete"


@dataclass(frozen=True)
class SourceClaim:
    """One claim with provenance preserved."""

    source: str
    date: str
    metric: str
    value: str
    available: bool = True


@dataclass(frozen=True)
class Finding:
    """A finding included in the generated briefing."""

    status: FindingStatus
    title: str
    claims: tuple[SourceClaim, ...]
    explanation: str


def meridian_sources(
    simulate_timeout: bool = False,
) -> list[SourceClaim]:
    """Return deterministic offline evidence for Meridian Logistics."""

    claims = [
        SourceClaim(
            source="Meridian Operations Report",
            date="2026-03-31",
            metric="on_time_delivery",
            value="95%",
        ),
        SourceClaim(
            source="Independent Logistics Audit",
            date="2026-04-15",
            metric="on_time_delivery",
            value="78%",
        ),
        SourceClaim(
            source="Meridian Capacity Report",
            date="2026-04-30",
            metric="warehouse_capacity",
            value="92%",
        ),
    ]

    if simulate_timeout:
        claims.append(
            SourceClaim(
                source="Regional Port Status Feed",
                date="2026-05-01",
                metric="port_disruption",
                value="source unavailable: simulated timeout",
                available=False,
            )
        )
    else:
        claims.append(
            SourceClaim(
                source="Regional Port Status Feed",
                date="2026-05-01",
                metric="port_disruption",
                value="No major disruption reported",
            )
        )

    return claims


def build_findings(
    claims: list[SourceClaim],
) -> list[Finding]:
    """Synthesize claims without hiding conflicts or failed sources."""

    available = [claim for claim in claims if claim.available]
    unavailable = [claim for claim in claims if not claim.available]

    delivery_claims = [
        claim
        for claim in available
        if claim.metric == "on_time_delivery"
    ]

    capacity_claims = [
        claim
        for claim in available
        if claim.metric == "warehouse_capacity"
    ]

    port_claims = [
        claim
        for claim in available
        if claim.metric == "port_disruption"
    ]

    findings: list[Finding] = []

    if capacity_claims or port_claims:
        established_claims = tuple(capacity_claims + port_claims)

        findings.append(
            Finding(
                status=FindingStatus.WELL_ESTABLISHED,
                title="Current logistics conditions",
                claims=established_claims,
                explanation=(
                    "Available operational sources provide attributable "
                    "evidence about current capacity and port conditions."
                ),
            )
        )

    if len({claim.value for claim in delivery_claims}) > 1:
        findings.append(
            Finding(
                status=FindingStatus.CONTESTED,
                title="On-time-delivery performance",
                claims=tuple(delivery_claims),
                explanation=(
                    "Sources report materially different delivery metrics. "
                    "Both values are retained with source and date rather "
                    "than being merged into a single unsupported estimate."
                ),
            )
        )

    if unavailable:
        findings.append(
            Finding(
                status=FindingStatus.INCOMPLETE,
                title="Unavailable source evidence",
                claims=tuple(unavailable),
                explanation=(
                    "The investigation completed despite source failure. "
                    "Unavailable evidence is explicitly marked incomplete."
                ),
            )
        )
    else:
        findings.append(
            Finding(
                status=FindingStatus.INCOMPLETE,
                title="Remaining evidence gaps",
                claims=(),
                explanation=(
                    "No supplier-level evidence was available to independently "
                    "validate every operational claim."
                ),
            )
        )

    return findings


def render_briefing(findings: list[Finding]) -> str:
    """Render the investigation with provenance attached to each claim."""

    sections: list[str] = []

    for status in FindingStatus:
        sections.append(f"## {status.value}")

        matching = [
            finding
            for finding in findings
            if finding.status == status
        ]

        if not matching:
            sections.append("No findings.")
            continue

        for finding in matching:
            sections.append(f"### {finding.title}")
            sections.append(finding.explanation)

            if not finding.claims:
                sections.append("- No attributable source claim available.")
                continue

            for claim in finding.claims:
                sections.append(
                    f"- {claim.metric}: {claim.value} "
                    f"[Source: {claim.source}; Date: {claim.date}]"
                )

    return "\n".join(sections)
