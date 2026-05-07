# Approval Verification Launch Evidence Pack

## Purpose

This document is the final pre-pilot evidence pack for go / no-go review.

It does not define new scope.
It records whether the current scope is launchable, observable, recoverable, auditable, and operable.

---

## 1. Scope of this evidence pack

Current launch-readiness scope assessed here:
- approval assistance only
- single attachment, single image
- SICK and MARRIAGE pilot-preparation scenarios
- no automatic approval / rejection
- manual final decision retained

---

## 2. Regression evidence

### 2.1 Targeted backend regression

Command executed:
- `python3.11 -m pytest tests/test_attachment_verification.py tests/test_marriage_certificate_parser.py -q`

Observed result:
- `25 passed`

Judgment:
- targeted backend regression baseline is green

### 2.2 Frontend build regression

Command executed:
- `npm run build` in `ui/approval-verification`

Observed result:
- build passed successfully

Judgment:
- current frontend bundle builds cleanly

---

## 3. Dataset and gating evidence

| Item | Evidence | Status |
|---|---|---|
| MARRIAGE dataset skeleton exists | `datasets/marriage/pass`, `datasets/marriage/review`, `datasets/marriage/weak` | Confirmed |
| MARRIAGE schema exists | `src/id_doc_ocr/plugins/marriage_certificate/schema.py` | Confirmed |
| MARRIAGE validator + pass gating exist | prior merged code + tests | Confirmed |
| MARRIAGE targeted regression baseline exists | targeted pytest coverage in repo | Confirmed |

Judgment:
- marriage gating is enabled and has minimum regression baseline coverage

---

## 4. Failure-state evidence

### Confirmed in this round
- analyze fail: rehearsed in V1, fail-closed with stale analysis warning
- verify fail: rehearsed in V1, fail-closed with stale verify warning
- non-image upload: blocked client-side with explicit message
- corrupted image: did not silently PASS; analyzed to reject/high risk in direct API checks
- repeated verify click: loading state disabled duplicate action
- backend unavailable on verify path: explicit error, stale result preserved as reference only
- malformed analyze response: parse failure surfaced, old analysis marked stale
- partial verify response: fail-closed with technical error; stale verify warning preserved
- fallback with no selected file: explicitly disclosed as demo sample fallback

### Still needing explicit launch evidence
- dedicated analyze-timeout drill
- dedicated analyze-backend-unavailable drill
- UI rehearsal for empty image file
- verify malformed-JSON drill as separate case from partial response

Judgment:
- failure-state coverage is materially improved, but not yet 100% closed

---

## 5. REVIEW process evidence

| Item | Evidence | Status |
|---|---|---|
| REVIEW SOP frozen in docs | `docs/review-sop.md` | Confirmed |
| review drill executed | `docs/review-drill-report.md` | Confirmed |
| marriage mismatch REVIEW rehearsed | V1 `REVIEW mock` | Confirmed |
| OCR weak / stale-state REVIEW behavior checked | browser drills + failure matrix | Confirmed |
| manual override policy defined | `docs/review-sop.md` | Confirmed in process |
| manual override product enforcement | no built-in persisted override UI flow observed | Not confirmed |

Judgment:
- REVIEW operation is process-ready, not yet product-enforced end to end

---

## 6. Metrics and operating cadence evidence

| Item | Evidence | Status |
|---|---|---|
| launch checklist exists | `docs/pilot-launch-checklist.md` | Confirmed |
| pilot metrics doc exists | `docs/pilot-metrics.md` | Confirmed |
| weekly review cadence defined | checklist + metrics docs | Confirmed in documentation |
| risk ledger schema frozen | `docs/pilot-metrics.md` | Confirmed |
| real roster / owner names frozen | not yet | Open |

Judgment:
- operating mechanism is documented; human ownership freeze still remains

---

## 7. Request tracing evidence

### Confirmed
- frontend adapter generates request_id and reuses it across analyze -> verify
- backend echoes request_id in successful responses
- backend logs request_id in analyze_input / analyze_result / verify_input / verify_result

### Not yet fully confirmed
- UI-visible requestId does not currently align with the real runtime request_id after live calls
- browser-side JS could not read `X-Request-Id` from live responses in current trace drill
- some 4xx error responses did not carry request_id
- REVIEW -> override audit chain still depends on external ledger discipline

Reference:
- `docs/request-id-tracing.md`

Judgment:
- request tracing is partially confirmed, not fully closed

---

## 8. Blocking / non-blocking issues for go-no-go

### Current blocking issues
1. UI-visible requestId is not yet aligned with runtime request_id
2. review / override audit path is process-defined but not product-enforced
3. pilot roster and named owners are still not frozen in real names
4. full failure-state evidence pack still lacks a few explicit launch drills

### Current non-blocking but important issues
1. some technical error messages are too raw for pilot operators
2. analyze/verify mixed-state view can still be cognitively heavy during failures
3. failure responses without request_id weaken incident audit

---

## 9. Launch judgment

Current state is best described as:
- technically runnable: Yes
- operationally prepared: Mostly
- fully auditable: Not yet
- safe for controlled pilot rehearsal: Yes
- safe for unrestricted pilot traffic: Not yet

Recommended go / no-go posture:
- Go for final launch rehearsal / kickoff freeze
- No-go for real pilot traffic until request_id display + owner freeze + override audit discipline are closed

---

## 10. Final evidence summary

| Evidence item | Status |
|---|---|
| regression executed | Confirmed |
| datasets exist | Confirmed |
| marriage gating enabled | Confirmed |
| failure-state validated | Partially confirmed with direct evidence |
| REVIEW SOP frozen | Confirmed |
| metrics cadence frozen in docs | Confirmed |
| fallback rehearsed | Confirmed |
| request_id tracing confirmed | Partially confirmed |

Overall conclusion:
- the project is no longer “just able to run”
- it is now close to pilot launch, but still has a small set of launch-governance and traceability gaps that should be closed before pilot traffic begins
