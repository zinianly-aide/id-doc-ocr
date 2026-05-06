# Approval Verification Pilot Metrics and Risk Ledger

## Purpose

This document freezes the minimum operating metrics and risk-ledger schema for the approval-verification pilot.

It is intentionally lightweight:
- no dashboard implementation
- no analytics pipeline design
- no code changes required

The goal is to make sure the team collects the same operational facts from day 1 of pilot traffic.

---

## 1. Metric scope

Current intended pilot scope for this metric definition:
- approval assistance only
- single attachment, single image
- leave scenarios currently entering pilot preparation:
  - SICK
  - MARRIAGE
- human approver keeps final decision authority

Operational rule:
- all metrics should be traceable at case level by case id and request_id where available

---

## 2. Core metrics

### 2.1 PASS rate

Definition:
- count of `verify_status = PASS` / total successful usable verification results

Why it matters:
- shows how much traffic is flowing through the low-friction path
- must be interpreted together with false-negative risk; higher PASS is not automatically better

### 2.2 REVIEW rate

Definition:
- count of `verify_status = REVIEW` / total successful usable verification results

Why it matters:
- monitors the size of manual-review burden
- abnormal REVIEW rate may indicate either over-conservative rules or unstable upstream extraction

### 2.3 Reject rate

Definition:
- count of `verify_status = REJECT` / total successful usable verification results

Why it matters:
- helps distinguish “uncertain but reviewable” from “clearly unacceptable” cases
- sudden spikes may indicate upstream input-quality changes or rule drift

### 2.4 Manual override rate

Definition:
- count of cases with human override / total successful usable verification results

Why it matters:
- high override means the system output is not aligning well with real approval judgment
- should be split later into:
  - approve-after-REVIEW
  - reject-after-REVIEW
  - exceptional release after REJECT

### 2.5 High-frequency risk Top 10

Definition:
- top 10 most frequent risk / warning / issue codes in the observation window

Suggested source fields:
- validation issue code
- rule result code
- explicit fallback reason code
- operator-entered misjudgment classification code

Why it matters:
- gives the team a concrete weekly prioritization list
- prevents optimization by anecdote only

### 2.6 OCR fail rate

Definition:
- count of cases where OCR / extraction is too weak for usable verification assistance / total pilot cases

Count as OCR fail when:
- unreadable image
- core fields not extractable
- review reason explicitly classified as OCR weak / unreadable

Why it matters:
- separates model / extraction weakness from downstream rule problems

### 2.7 Verify fail rate

Definition:
- count of verification requests that fail to return a usable business result / total pilot verify attempts

Include:
- backend unavailable
- timeout
- runtime failure
- unusable verification response
- stale-result-only recovery path after failed retry

Why it matters:
- this is the most direct operational-availability metric for the approval flow

### 2.8 Average review handling time

Definition:
- average elapsed time from approver opening a REVIEW case to final human action recorded

Suggested start:
- REVIEW result visible to approver

Suggested end:
- final action recorded: approve, reject, return for correction, or escalate

Why it matters:
- reveals whether REVIEW is operationally manageable
- a pilot with safe outputs but unmanageable handling time is not truly launch-ready

---

## 3. Minimum daily metric snapshot

The team should be able to produce this snapshot daily during launch week if traffic exists:

| Metric | Daily output required |
|---|---|
| Total pilot cases | integer |
| PASS rate | percentage |
| REVIEW rate | percentage |
| Reject rate | percentage |
| Manual override rate | percentage |
| OCR fail rate | percentage |
| Verify fail rate | percentage |
| Average review handling time | minutes |
| Top risks | top 5 for the day |

---

## 4. Weekly metric review pack

Weekly review should include:
1. total volume and scenario mix
2. PASS / REVIEW / REJECT distribution
3. override distribution
4. OCR fail and verify fail trends
5. average and worst review handling time
6. top 10 risk codes
7. top misjudgment examples
8. open actions from previous week and closure status

Weekly interpretation rule:
- never read a rate alone
- every abnormal rate should be paired with at least one concrete case example

---

## 5. Risk ledger schema

Minimum ledger fields:

| Field | Description |
|---|---|
| date | case review date |
| case_id | business case id |
| request_id | technical request trace id, if available |
| leave_type | SICK / MARRIAGE / other pilot scope |
| risk_code | normalized issue / warning / rule / fallback code |
| decision | system decision: PASS / REVIEW / REJECT / FAIL |
| reviewer_action | final human action: approve / reject / return / escalate |
| override | yes / no |
| override_note | required if override = yes |
| root_cause | OCR / parser / validator / business policy / integration / operator misuse / unknown |
| follow_up_action | no action / watch / training / data / rule fix / bug fix / policy clarification |

Recommended extra fields:

| Field | Description |
|---|---|
| reviewer_name | who handled the case |
| review_owner | owner of the queue at time of handling |
| severity | low / medium / high / critical |
| image_quality_bucket | clear / weak / unreadable |
| attachment_type_seen | what document the system believed it saw |
| final_outcome_note | short human-readable summary |
| closed_at | when follow-up was considered closed |

---

## 6. Ledger coding rules

### decision field
Use one of:
- PASS
- REVIEW
- REJECT
- FAIL

### reviewer_action field
Use one of:
- approve
- reject
- return_for_correction
- escalate
- manual_fallback

### root_cause field
Use one primary root cause only:
- OCR
- parser
- validator
- business_policy
- integration
- operator_misuse
- unknown

### follow_up_action field
Use one primary next action:
- none
- monitor
- training_update
- data_update
- rule_change_candidate
- bug_fix_candidate
- policy_clarification

This keeps the first pilot ledger simple enough to maintain consistently.

---

## 7. Ownership and cadence

| Item | Owner | Cadence |
|---|---|---|
| Daily metric collection | QA + Pilot Operations Support | every pilot business day |
| Weekly metric summary | Metrics Owner + Pilot Operations Support | weekly |
| Risk ledger maintenance | Pilot Operations Support | rolling, same day for high-risk cases |
| Misjudgment classification review | QA + Product / Process Lead + HR / Policy Expert | weekly |
| Go / no-go interpretation | Business Owner | weekly / incident driven |

Suggested operating cutoffs:
- daily data cut-off: 18:00 CST
- weekly review: Wednesday 16:00 CST
- severe false-pass escalation: same day, immediate

---

## 8. Minimum launch requirement

Do not call the pilot “operationally launched” unless the team can do all of the following consistently:
1. record every pilot case with case id
2. trace technical incidents by request_id where available
3. produce daily PASS / REVIEW / REJECT counts
4. record every override with note
5. maintain a risk ledger with root cause and follow-up action
6. review abnormal metrics with real case examples every week

If these six conditions are not met, the project is still in launch preparation, not operational pilot mode.
