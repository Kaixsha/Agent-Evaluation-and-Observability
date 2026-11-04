"""Tests for provenance-preserving supply-chain synthesis."""

from supply_chain_risk.investigation import (
    FindingStatus,
    build_findings,
    meridian_sources,
    render_briefing,
)


def test_normal_run_has_all_three_sections() -> None:
    claims = meridian_sources()
    findings = build_findings(claims)
    briefing = render_briefing(findings)

    assert "## Well-Established" in briefing
    assert "## Contested" in briefing
    assert "## Incomplete" in briefing


def test_conflicting_delivery_values_are_both_retained() -> None:
    claims = meridian_sources()
    findings = build_findings(claims)
    briefing = render_briefing(findings)

    assert "95%" in briefing
    assert "78%" in briefing
    assert "Meridian Operations Report" in briefing
    assert "Independent Logistics Audit" in briefing
    assert "2026-03-31" in briefing
    assert "2026-04-15" in briefing


def test_delivery_conflict_is_classified_as_contested() -> None:
    claims = meridian_sources()
    findings = build_findings(claims)

    contested = [
        finding
        for finding in findings
        if finding.status == FindingStatus.CONTESTED
    ]

    assert len(contested) == 1
    assert contested[0].title == "On-time-delivery performance"
    assert len(contested[0].claims) == 2


def test_source_timeout_does_not_abort_run() -> None:
    claims = meridian_sources(simulate_timeout=True)
    findings = build_findings(claims)
    briefing = render_briefing(findings)

    assert "## Incomplete" in briefing
    assert "Regional Port Status Feed" in briefing
    assert "simulated timeout" in briefing


def test_timeout_source_is_marked_unavailable() -> None:
    claims = meridian_sources(simulate_timeout=True)

    failed = [
        claim
        for claim in claims
        if not claim.available
    ]

    assert len(failed) == 1
    assert failed[0].source == "Regional Port Status Feed"


def test_provenance_is_preserved_in_briefing() -> None:
    claims = meridian_sources()
    findings = build_findings(claims)
    briefing = render_briefing(findings)

    assert "[Source: Meridian Operations Report; Date: 2026-03-31]" in briefing
    assert "[Source: Independent Logistics Audit; Date: 2026-04-15]" in briefing
