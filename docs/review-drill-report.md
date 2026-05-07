# REVIEW Flow Drill Report

## Purpose

This document records a structured drill of the REVIEW path before pilot launch.

Goal:
- confirm REVIEW contains enough information for an approver to act
- check whether override can be audited
- check whether metrics / ledger fields can capture the case consistently

Evidence basis in this round:
- V1 page rehearsal in real-adapter mode
- REVIEW SOP cross-check
- current metric / risk-ledger schema cross-check

---

## 1. Drill case: Marriage mismatch REVIEW

### Scenario
- V1 page switched to `REVIEW mock`
- request header showed `leaveType = MARRIAGE`
- attachment type shown as `marriage_certificate`
- verification panel showed `REVIEW / MEDIUM`

### What the approver can see now
- business verification result is visible as REVIEW
- risk level is visible
- attachment type match is visible
- request-side evidence includes leave type, applicant name, related person name / relation, leave dates
- current card language says manual review is needed

### What is good
- REVIEW state is explicit, not hidden
- business conclusion is visually separated from analysis suggestion
- marriage review scenario is understandable enough for a reviewer to know this is not direct-pass

### What is weak
- the page is still better at showing the existence of REVIEW than showing a complete operational next step
- mismatch-specific audit capture is not built in
- no built-in override record or review note is captured in-product

### Drill judgment
- REVIEW information sufficiency: Partial pass
- operator next-step clarity: acceptable only with `docs/review-sop.md` training
- auditability: process-only, not system-enforced

Severity:
- Medium

Blocking?
- Not blocking by itself if SOP and ledger are frozen before launch

---

## 2. Drill case: OCR weak REVIEW

### Scenario
Observed via analysis/review content and failure-state drills where OCR / extraction uncertainty remained visible and manual review guidance was shown.

### What the approver can see now
- review-oriented analysis suggestion
- warnings / risk prompts
- structured fields with missing / weak extraction patterns
- stale/reference wording when latest analyze is not reliable

### What is good
- the system does not silently PASS weak OCR conditions in the tested drills
- stale analysis wording clearly warns against trusting the old analysis as current truth

### What is weak
- the UI does not convert OCR-weak cases into a single standardized operator action block automatically
- the approver still needs SOP context to decide between return-for-correction vs manual confirmation

### Drill judgment
- REVIEW information sufficiency: Pass
- operator next-step clarity: Partial pass
- auditability: process-only

Severity:
- Medium

Blocking?
- Not blocking if SOP training is completed before pilot start

---

## 3. Drill case: analyze rejected REVIEW

### Scenario
- V1 page `REVIEW mock` + real-adapter analyze execution
- latest analysis moved to `reject / high`
- verification remained separately represented
- on analyze failure or malformed analyze response, the page explicitly labeled old analysis as stale

### What the approver can see now
- analysis and verification are not merged into one ambiguous status
- failure wording makes it clear that the current analysis card may be old
- the page warns against treating stale analysis as latest recognition result

### What is good
- fail-closed behavior is visible
- stale analysis warning is explicit
- operator is less likely to mistake stale analysis for the latest decision basis

### What is weak
- mixed state can still be cognitively heavy: stale analysis + existing verification + technical error message
- no dedicated operator summary panel tells the approver exactly whether to stop, re-run, or escalate

### Drill judgment
- REVIEW information sufficiency: Pass
- operator next-step clarity: Partial pass
- auditability: Partial

Severity:
- Medium

Blocking?
- Not blocking, but should be included in kickoff training examples

---

## 4. Drill case: manual override

### Scenario
No built-in override workflow was executed in-product during this round.
The drill therefore evaluated override readiness against current SOP + metrics docs.

### What exists today
- `docs/review-sop.md` defines who may override and what fields must be recorded
- `docs/pilot-metrics.md` defines override and override_note in the risk ledger schema

### What does not yet exist in-product
- no visible override form or enforced comment field in the UI
- no built-in linkage from REVIEW result to persisted override record
- no built-in audit surface proving which approver overrode which case

### Drill judgment
- override policy definition: Pass (documented)
- override product enforcement: Fail (not implemented)
- override auditability: Partial, depends on external ledger discipline

Severity:
- High for pilot governance

Blocking?
- Yes, unless the team freezes an external review/override ledger and makes it mandatory in launch SOP

---

## 5. Can metrics record these REVIEW cases?

Current answer:
- yes in process terms, if the team uses the ledger defined in `docs/pilot-metrics.md`
- no in product-enforced terms, because the UI does not currently write the review / override event into a ledger automatically

Therefore:
- metrics readiness is operationally possible
- metrics readiness is not yet system-enforced

---

## 6. Overall drill summary

| Drill item | Result | Notes |
|---|---|---|
| Marriage mismatch REVIEW | Partial pass | review visible, but actionability still depends on SOP |
| OCR weak REVIEW | Pass / Partial | safe enough, but next-step guidance still depends on training |
| Analyze rejected / stale analysis REVIEW | Pass / Partial | safe-fail wording is good; mixed-state cognitive load still exists |
| Manual override | Partial / Fail | documented in process, not enforced in product |

---

## 7. Key conclusions

1. REVIEW is visible enough for pilot rehearsal.
2. REVIEW is not yet fully self-sufficient; approvers still need SOP support.
3. Stale-state wording is one of the stronger parts of the current implementation.
4. Override remains the biggest governance gap because it is only process-defined.
5. Pilot launch is still possible only if the team accepts a process-led audit path outside the product UI.

---

## 8. Immediate launch actions

Before pilot traffic, do all of the following:
1. train approvers on at least these 3 drill cases:
   - marriage mismatch
   - OCR weak
   - stale verify result after failure
2. freeze one mandatory external ledger for REVIEW and override recording
3. require request_id or case_id in every manual override record
4. include these drill outcomes in the go / no-go meeting
