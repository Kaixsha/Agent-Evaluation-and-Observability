# Agent-Evaluation-and-Observability
## Project Submission

This project demonstrates reliability and observability across three reference-style systems using the reproduce, run, perturb, and reflect workflow.

### System 1: Validated and Routed Policy Extraction

Location:

`system1-policy-extractor/`

Demonstrates:

- Validation-driven retry
- Batch processing
- Deterministic routing
- `auto_approve`, `spot_check`, and `human_review`
- Independent routing signals
- Sliced calibration analysis

Evidence:

`evidence/system1/`

### System 2: Schema-Enforced Mortgage Extraction

Location:

`system2-mortgage-extractor/`

Demonstrates:

- Document classification
- Two-pass structured extraction
- Schema enforcement
- Missing values preserved as null
- Informal unit normalization
- Arithmetic consistency validation

Evidence:

`evidence/system2/`

### System 3: Provenance-Preserving Supply-Chain Investigation

Location:

`system3-supply-chain-risk/`

Demonstrates:

- Multi-source synthesis
- Source attribution and dates
- Well-Established, Contested, and Incomplete findings
- Preservation of conflicting metrics
- Graceful source-failure handling

Evidence:

`evidence/system3/`

## Submission Documentation

- `environment-note.md` - execution environment information
- `perturbation-log.md` - controlled edge-case experiments for all three systems
- `reflection.md` - analysis of evaluation, reliability, observability, and lessons learned
- `evidence/` - captured test, static-analysis, behavioral, and perturbation outputs

## Key Observed Results

- System 1 routing: 2 `auto_approve`, 1 `human_review`, and 1 `spot_check`
- System 1 calibration: `umbrella / exclusions` showed confidence `0.93` but observed accuracy `0.00`
- System 2 normalization: `about 2,400 sq ft` became `2400`
- System 2 missing field: missing bonus remained `null`
- System 2 consistency check: calculated total `70000` versus stated total `75000`, producing a `5000` discrepancy
- System 3 conflict: on-time-delivery values of `95%` and `78%` were both retained with provenance
- System 3 timeout: the investigation completed while the failed source was explicitly represented as incomplete
