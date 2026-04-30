# RISKS

## Scope

This document defines the minimum risk and rollback controls for the current pilot-launch stage.

Frozen scope:
- scenario: `SICK` only
- attachment: single image
- usage mode: approval assistance only
- final decision: human approver retained

---

## 1. False-Pass Risk

### Description
A weak, incomplete, or non-standard attachment is surfaced as PASS and is trusted too easily by the approver.

### Why it matters
This is the highest pilot-safety risk because it may create an operational false release.

### Signals
- business-side incident where PASS should have gone to REVIEW or rejection
- repeated weak-image cases still appearing as PASS
- approvers reporting low trust in PASS stability

### Control
- keep manual authority with approver
- require weekly review of PASS incidents and disputed cases
- use sample registry and incident examples to classify recurring patterns

### Rollback trigger
- any confirmed severe false-pass case in the pilot window that business owner judges unacceptable
- or repeated false-pass pattern without a same-week containment decision

---

## 2. REVIEW-Rate Abnormality Risk

### Description
REVIEW rate becomes abnormally low or high in real pilot traffic.

### Why it matters
- too low may indicate over-release risk
- too high may indicate weak business value and excessive manual burden

### Signals
- REVIEW rate < 10%
- REVIEW rate > 45%
- business team reports that review volume is operationally unusable

### Control
- review rate daily during launch week if traffic exists
- interpret together with incident samples, not as a standalone metric
- do not treat lower REVIEW rate as automatically better

### Rollback trigger
- REVIEW rate stays outside acceptable range for the agreed observation window and business owner rejects continued exposure

---

## 3. Interface Failure Risk

### Description
The integration path fails to return a usable verification result, or returns an unusable error state.

### Why it matters
The pilot cannot operate if approvers repeatedly hit failures or must trust stale data.

### Signals
- success rate < 95%
- repeated timeout / backend unavailable / runtime error
- stale-result handling becomes common

### Control
- clear UI error state
- stale output must be marked reference-only
- immediate fallback to manual handling
- log every incident with request_id

### Rollback trigger
- success rate drops below launch threshold for the agreed observation window
- or repeated incidents prevent approvers from completing the workflow safely

---

## 4. request_id Traceability Failure Risk

### Description
Cases cannot be traced end to end because request_id is missing, inconsistent, or not searchable.

### Why it matters
Without traceability, weekly review, incident diagnosis, and rollback judgment become unreliable.

### Signals
- incident screenshots cannot be mapped back to a request log
- response lacks request_id
- logs cannot be searched by request_id

### Control
- generate request_id before service invocation
- echo request_id in response
- include request_id in logs, issue tracking, and operator evidence records

### Rollback trigger
- any significant incident cannot be traced because request_id is unavailable
- or request tracing is found non-operational during launch rehearsal

---

## 5. Manual Fallback Breakdown Risk

### Description
Approvers do not know how to continue safely when the system returns REVIEW, REJECT, OCR failure, or interface failure.

### Why it matters
A pilot with fallback confusion is not operationally safe even if the model works technically.

### Signals
- approvers ask for ad hoc handling rules
- inconsistent handling of REVIEW or stale/error cases
- operations support cannot classify incidents consistently

### Control
- train approvers on frozen SOP
- keep fallback path identical: manual handling first
- keep weekly issue review for confusing cases

### Rollback trigger
- pilot users cannot consistently execute fallback handling during rehearsal or launch week

---

## 6. Global Rollback Rule

Rollback means:
- stop treating the verification output as an active pilot-assistance capability for new pilot cases
- continue the underlying leave-approval process manually
- keep collecting incident evidence for diagnosis

Pilot rollback should be triggered when any of the following is true:
1. a severe false-pass incident is confirmed
2. request_id tracing is non-operational
3. interface failure rate causes success rate to fall below threshold
4. REVIEW-rate abnormality makes business owner reject continued pilot exposure
5. fallback handling is not executable by approvers

---

## 7. Ownership

- Risk owner: Business Owner + Product / Process Lead
- Technical response: Backend Engineer / Frontend Engineer
- Operational response: Pilot Operations Support
- Final rollback decision: Business Owner
