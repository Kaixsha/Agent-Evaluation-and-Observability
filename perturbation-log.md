# Perturbation Log

## System 1: Validated and Routed Policy Extraction

### Deliberate change
I tested a policy extraction where the required `premium_amount` field was deliberately returned as `null`.

### Command
`.venv/bin/pytest tests/test_us01_retry.py -v`

### Observed behavior
The validation safeguard detected the missing required field. When the value was recoverable, the pipeline retried the extraction and succeeded on the second attempt. When the required value remained missing, the record was escalated to `human_review`.

### Comparison with unperturbed input
On normal input with all required fields present and high confidence, the pipeline routes the record to `auto_approve` without requiring the same recovery path.

### Evidence
`evidence/system1/perturbation-retry.txt`

---

## System 2: Schema-Enforced Mortgage Extraction

### Deliberate change
I used an income document in which the stated total was deliberately inconsistent with the extracted line items.

The line items were:

- Base salary: 60000
- Overtime: 5000
- Bonus: 5000

Their calculated sum was `70000`, while the stated total was `75000`.

### Command
`.venv/bin/mortgage-extract fixtures/documents/income_sum_mismatch.txt --mode replay`

### Observed behavior
The extraction completed successfully, but the arithmetic consistency validator reported a discrepancy of `5000`.

### Comparison with unperturbed input
The clean appraisal input was processed without an arithmetic discrepancy and normalized the informal text `about 2,400 sq ft` to the integer `2400`.

### Evidence
`evidence/system2/perturbation.txt`
`evidence/system2/sum-mismatch.txt`
`evidence/system2/appraisal.txt`

---

## System 3: Provenance-Preserving Supply-Chain Investigation

### Deliberate change
I enabled the source-failure simulation using `--simulate-timeout`.

### Command
`.venv/bin/supply-chain-investigate meridian --offline --simulate-timeout`

### Observed behavior
The investigation did not abort. The failed `Regional Port Status Feed` was preserved as unavailable evidence and appeared in the `Incomplete` section of the briefing.

### Comparison with unperturbed input
Without `--simulate-timeout`, the regional port source returned normally and contributed evidence about port conditions. With the perturbation enabled, the rest of the investigation still completed, including the `Well-Established` and `Contested` findings.

### Evidence
`evidence/system3/perturbation.txt`
`evidence/system3/simulated-timeout.txt`
`evidence/system3/meridian_briefing_timeout.md`
