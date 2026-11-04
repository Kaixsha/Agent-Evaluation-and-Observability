# Reflection

## Overview

In this project, I reproduced, ran, perturbed, and evaluated three systems that demonstrate different reliability and observability techniques for AI-assisted workflows. Rather than only checking whether the systems produced outputs, I examined how each system responded to invalid data, uncertainty, conflicting evidence, and source failure.

The three systems demonstrated complementary reliability principles:

1. A validated insurance-policy extraction pipeline with deterministic human-review routing.
2. A schema-enforced two-pass mortgage document extractor with arithmetic consistency validation.
3. A provenance-preserving multi-source supply-chain investigation pipeline that retains conflicting evidence and tolerates source failure.

My evidence pack contains the outputs from tests, static analysis, normal runs, and controlled perturbations for each system.

---

## System 1: Validated and Routed Policy Extraction

### Reproduction and Verification

I verified the policy extraction implementation using its automated tests and static-analysis tools.

The test run recorded in `evidence/system1/pytest.txt` completed with 25 passing tests in my rebuilt implementation. The static-analysis runs are recorded in `evidence/system1/mypy.txt` and `evidence/system1/ruff.txt`, with no remaining reported errors.

The full pipeline output is recorded in `evidence/system1/pipeline.txt`, and the generated routing decisions are stored in `evidence/system1/routing_decisions.json`.

The observed routing counts were:

- `auto_approve: 2`
- `human_review: 1`
- `spot_check: 1`

This demonstrated that the system does not treat every extraction equally. Records can proceed automatically, be sampled for checking, or be escalated for human review depending on independent validation and routing signals.

### Validation-Driven Retry

The targeted retry behavior is captured in `evidence/system1/perturbation-retry.txt`.

I deliberately exercised a case where the required `premium_amount` field was null. The validator detected the invalid extraction instead of allowing it to pass silently.

When a valid value could be recovered, the pipeline retried and successfully processed the policy on the second attempt. When the required value remained unavailable, the validation failure resulted in escalation rather than fabrication.

This behavior showed me that retry should be driven by a specific validation failure rather than blindly repeating a model request.

### Human-in-the-Loop Routing

One especially important result came from policy `POL-003` in `evidence/system1/routing_decisions.json`.

The record had a confidence value of `0.99`, but it was still routed to `human_review` because the independent signal `independent_extractor_disagreement` was true.

This result is important because confidence alone should not determine whether automation is safe. A model can be highly confident while another independent safeguard identifies a disagreement. In this case, the independent disagreement appropriately overrode the high confidence score.

### Calibration

The calibration results in `evidence/system1/calibration.txt` showed:

- `auto / premium_amount`: confidence `0.95`, accuracy `1.00`
- `home / deductible`: confidence `0.90`, accuracy `1.00`
- `umbrella / exclusions`: confidence `0.93`, accuracy `0.00`
- Overall Brier score: `0.291`

The most important result was the `umbrella / exclusions` slice. Even though its predicted confidence was `0.93`, its observed accuracy was `0.00`.

This demonstrates why aggregate evaluation numbers are not sufficient. The overall Brier score can appear moderate while a particular policy-type and field combination performs very poorly. In a production system, I would therefore monitor calibration by meaningful slices instead of relying only on one overall accuracy or confidence statistic.

---

## System 2: Schema-Enforced Two-Pass Mortgage Extraction

### Structured Extraction

The mortgage extraction system first classifies the document and then produces a schema-constrained extraction.

The run captured in `evidence/system2/appraisal.txt` processed the informal phrase:

`about 2,400 sq ft`

and normalized it to:

`2400`

This demonstrated that the extractor could convert informal document text into a consistent structured representation.

### Missing Information and Non-Fabrication

The missing-field example is recorded in `evidence/system2/missing-bonus.txt`.

The source document did not provide a bonus value. The structured extraction therefore returned:

`"bonus": null`

rather than estimating or inventing a bonus.

I consider this an important reliability property. A missing value and a zero value do not mean the same thing. Returning null preserves the uncertainty in the source document and allows another system or a human reviewer to recognize that the information was unavailable.

Fabricating a plausible numeric value would make the output appear more complete while actually making it less trustworthy.

### Arithmetic Consistency Validation

The arithmetic edge case is recorded in `evidence/system2/sum-mismatch.txt`.

The extracted line items were:

- Base salary: `60000`
- Overtime: `5000`
- Bonus: `5000`

The calculated line-item sum was therefore:

`70000`

However, the stated total in the source document was:

`75000`

The consistency validator reported a discrepancy of:

`5000`

This demonstrated the value of validating structured output against relationships between fields. Each individual number was syntactically valid, but the collection of values was internally inconsistent.

Without the arithmetic check, the extraction could appear successful even though the document contained a significant inconsistency.

### Perturbation

The normal-versus-perturbed comparison is captured in `evidence/system2/perturbation.txt`.

The clean appraisal input was processed normally and its informal square-foot measurement was normalized to `2400`.

In the deliberately inconsistent income input, extraction still completed, but the consistency safeguard identified the difference between the `70000` calculated line-item total and the `75000` stated total.

This showed that validation should not only check whether fields exist or match a schema. It should also check meaningful domain relationships between those fields.

---

## System 3: Provenance-Preserving Multi-Source Synthesis

### Normal Investigation

The normal investigation run is recorded in `evidence/system3/investigation.txt`, and the generated briefing is stored in `evidence/system3/meridian_briefing.md`.

The briefing separates findings into:

- Well-Established
- Contested
- Incomplete

This structure makes uncertainty visible instead of presenting every statement with the same level of confidence.

### Conflicting Metrics

The most important contested evidence was the on-time-delivery metric.

The Meridian Operations Report dated `2026-03-31` reported:

`95%`

while the Independent Logistics Audit dated `2026-04-15` reported:

`78%`.

Both values are preserved in the briefing with their source and date rather than being averaged or reconciled into a single number.

I would not combine these numbers into one value because the evidence does not establish which source is authoritative or whether both sources used the same measurement definition, population, or reporting period.

Averaging the two figures would create a new value that neither source actually reported. Preserving both values maintains provenance and makes the disagreement observable for a reviewer.

### Source Failure

The source-failure run is captured in `evidence/system3/simulated-timeout.txt` and `evidence/system3/meridian_briefing_timeout.md`.

When I ran the investigation with `--simulate-timeout`, the Regional Port Status Feed became unavailable.

The investigation did not abort.

Instead, the failed source was retained and represented in the `Incomplete` section as unavailable because of the simulated timeout.

The normal-versus-failure comparison is also captured in `evidence/system3/perturbation.txt`.

This behavior is useful for reliability because one unavailable source should not necessarily prevent all other valid evidence from being synthesized. At the same time, silently dropping the failed source would be misleading. Explicitly recording the failure makes degraded evidence quality visible to the user.

---

## Evaluation and Observability Tradeoffs

Across the three systems, I observed that reliability requires more than checking whether a program completed successfully.

System 1 demonstrated that a high confidence score is not enough. `POL-003` had confidence `0.99`, but an independent disagreement signal still caused `human_review`. The sliced calibration report also showed that `umbrella / exclusions` had confidence `0.93` but accuracy `0.00`.

System 2 demonstrated that valid-looking structured fields can still be unreliable when relationships between fields are inconsistent. The `5000` discrepancy was only visible because the system checked the arithmetic relationship between the extracted components and stated total.

System 3 demonstrated that evidence quality depends on provenance. The `95%` and `78%` delivery values should not be silently merged because doing so would hide a real conflict between two attributed sources.

These observations show that better observability can expose weaknesses that a simple success/failure metric would hide.

---

## Reliability Principle I Would Apply to My Own Work

The main reliability principle I would apply to my own systems is:

**Do not hide uncertainty or inconsistency. Make it observable and route it appropriately.**

The three systems implement this principle at different levels.

System 1 makes uncertainty operational by routing questionable records to human review.

System 2 makes uncertainty structural by preserving missing fields as null and detecting relationships that do not reconcile.

System 3 makes uncertainty evidential by preserving conflicting source values and explicitly marking unavailable evidence.

Together, these systems showed me that reliable AI systems should not be designed only to produce an answer. They should also provide enough evidence to understand when that answer should not be trusted automatically.

For work involving data analytics, application support, or automated extraction, I would therefore combine schema validation, deterministic checks, independent signals, provenance, and human escalation rather than relying on model confidence alone.

---

## Evidence Summary

The main artifacts supporting this reflection are:

### System 1
- `evidence/system1/pytest.txt`
- `evidence/system1/mypy.txt`
- `evidence/system1/ruff.txt`
- `evidence/system1/pipeline.txt`
- `evidence/system1/routing_decisions.json`
- `evidence/system1/calibration.txt`
- `evidence/system1/perturbation-retry.txt`
- `evidence/system1/environment.txt`

### System 2
- `evidence/system2/pytest.txt`
- `evidence/system2/mypy.txt`
- `evidence/system2/ruff.txt`
- `evidence/system2/appraisal.txt`
- `evidence/system2/missing-bonus.txt`
- `evidence/system2/sum-mismatch.txt`
- `evidence/system2/perturbation.txt`
- `evidence/system2/environment.txt`

### System 3
- `evidence/system3/pytest.txt`
- `evidence/system3/mypy.txt`
- `evidence/system3/ruff.txt`
- `evidence/system3/investigation.txt`
- `evidence/system3/meridian_briefing.md`
- `evidence/system3/simulated-timeout.txt`
- `evidence/system3/meridian_briefing_timeout.md`
- `evidence/system3/perturbation.txt`
- `evidence/system3/environment.txt`

The evidence pack, perturbation log, environment note, and this reflection collectively document what I ran, what I observed, which safeguards activated, and why those safeguards improve reliability.
