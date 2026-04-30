# METRICS

## Scope

This document defines the minimum operating metrics for the current pilot-launch stage.

Frozen scope for these metrics:
- scenario: `SICK` only
- attachment: single image
- usage mode: approval assistance only
- pilot window: small-scope pilot approvers only

This document is for pilot operation, not model training or algorithm benchmarking.

---

## 1. Success Rate

### Definition
- successful usable verification results / total pilot verification requests

### Numerator
A request counts as successful only if:
- the verification request completes,
- the UI receives a usable business result,
- the approver can continue with PASS / REVIEW / REJECT semantics,
- the result is not merely a stale prior result.

### Denominator
- all pilot verification requests triggered in the SICK pilot window

### Exclude from numerator but include in denominator
- interface failure
- timeout
- internal verification runtime failure
- unusable error response
- stale-result-only display after failed retry

### Purpose
- measures whether the pilot is operationally usable, not just technically reachable

### Initial target
- target: `>= 95%`

---

## 2. REVIEW Rate

### Definition
- count of `verify_status = REVIEW` / total successful usable verification results

### Purpose
- monitors whether the pilot is too permissive or too conservative

### Interpretation band
- healthy observation band: `15% ~ 35%`
- below `10%`: likely under-review risk
- above `45%`: likely weak business efficiency value

### Operational note
- REVIEW rate must be interpreted together with sample mix and false-pass incidents
- do not optimize toward lower REVIEW blindly

---

## 3. P95 Latency

### Definition
- P95 elapsed time from approver trigger to usable verification result visible in UI

### Measurement start
- when the approver initiates verification

### Measurement end
- when the approver can see a usable PASS / REVIEW / REJECT result or a clearly handled error state

### Initial target
- end-to-end P95: `< 8s`
- analyze target reference: `< 5s`
- verify target reference: `< 3s`

### Purpose
- ensures the pilot is not only correct enough but also operationally usable during approval flow

---

## 4. Manual Review Ratio

### Definition
- count of cases that actually require human manual handling / total pilot cases

### Count as manual review required when
- `verify_status = REVIEW`
- `verify_status = REJECT`
- OCR failure occurs
- verification request fails and the case falls back to manual handling
- stale-result condition prevents trusting the latest system output

### Purpose
- measures real operational load on approvers and pilot support

### Initial target band
- `20% ~ 40%`

### Interpretation
- if too low, safety may be weak
- if too high, business value may be weak

---

## 5. Collection Rule

For the first pilot stage, the minimum per-case record should include:
- request_id
- trigger time
- result time
- verify_status or error_code
- whether manual review was required
- whether the case was counted as successful usable verification

---

## 6. Review Cadence

### During launch week
- daily review if pilot traffic exists

### After launch week
- weekly review in the pilot status meeting

### Immediate escalation
- if rollback triggers in `docs/RISKS.md` are hit

---

## 7. Ownership

- Metric owner: Product / Process Lead
- Data support: Backend Engineer / Frontend Engineer / Pilot Operations Support
- Acceptance reviewer: Business Owner / QA

---

## 8. Minimum launch requirement

The pilot should not be treated as operationally launched unless all four metrics can be recorded with the same `request_id` trace basis.

---

## 9. 首轮采集样例

### Collection setup

- validation batch size: `10`
- executed in P3.1 pre-launch validation
- request mode: caller-generated `request_id`, then analyze -> verify with the same ID
- sample mix:
  - PASS rehearsal path: 5 Normal samples
  - manual-review rehearsal path: 5 mixed Abnormal / Edge samples

### Minimum recorded fields

For each case, the batch recorded:
- `request_id`
- `verify_status`
- whether manual review was required
- interface latency (`verify_latency_ms`)

### First-round observed result

- success rate: `10 / 10 = 100%`
- REVIEW rate: `5 / 10 = 50%`
- manual review ratio: `5 / 10 = 50%`

### Simple latency distribution

`verify_latency_ms` in the first collected batch:
- min: `8.31 ms`
- median: `114.17 ms`
- p95: `735.89 ms`
- max: `802.14 ms`

### Interpretation note

- this first-round collection proves the metric collection path is operable
- this is still a validation batch, not a production pilot baseline
- the batch intentionally covered both PASS and REVIEW handling branches so that approval actions and manual-review counting could be checked end to end
