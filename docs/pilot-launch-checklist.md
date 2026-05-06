# Approval Verification Pilot Launch Checklist

## Purpose

This checklist is the operational gate for moving approval-verification from “technically runnable” to “pilot-launchable”.

It is intended for the kickoff meeting and the final go / no-go review before exposing the workflow to real approvers.

Current technical baseline assumed by this checklist:
- SICK leave MVP chain is complete
- frontend/backend real integration has been validated
- real mode is the default operating mode
- MARRIAGE minimum gating and regression baseline are checked in
- final approval authority remains with human approvers

Go / no-go rule:
- if any P0 item below is still Open, do not start pilot traffic
- if any P1 item below is still Open, launch only with explicit Business Owner sign-off

---

## 1. Personnel and ownership freeze

| Item | Why it matters | Owner | Required action | Status |
|---|---|---|---|---|
| Pilot approver roster is confirmed with real names | Pilot cannot start on placeholder roster | Business Owner + HR / Policy Expert | Freeze approver list, department, backup approver, and pilot start window | Open |
| REVIEW owner is named | REVIEW cannot be an unowned queue | Product / Process Lead | Name first-line REVIEW owner and backup | Open |
| Escalation owner is named | High-risk cases need a single escalation path | Business Owner | Name escalation approver for policy disputes / severe risk | Open |
| Weekly review owner is named | Weekly review drifts if it is shared by everyone and owned by no one | Pilot Operations Support | Own meeting invite, agenda, minutes, and action follow-up | Open |
| Metrics owner is named | Metrics definitions are useless without a named operator | Product / Process Lead | Own metric definition freeze and weekly metric sign-off | Open |
| Engineering support owner is named | Pilot incidents need a technical responder | Backend Engineer + Frontend Engineer | Name one primary support contact for launch week | Open |
| QA evidence owner is named | Misjudgment review requires stable evidence collection | QA | Own replay evidence, screenshots, and case-log completeness check | Open |

Decision gate:
- launch only after the approver roster, REVIEW owner, escalation owner, and weekly review owner are all explicitly named

---

## 2. REVIEW operating mechanism

| Item | Why it matters | Owner | Required action | Status |
|---|---|---|---|---|
| REVIEW handling path is frozen | Approvers need one path, not ad hoc judgment | Product / Process Lead + HR / Policy Expert | Confirm what happens after REVIEW: inspect, request correction, approve with manual confirmation, or reject | Draft |
| REVIEW SLA is frozen | REVIEW queue must not silently accumulate | Business Owner | Set SLA for first response and same-day closure expectation | Open |
| REVIEW escalation rule is frozen | Stuck REVIEW cases need escalation timing | Escalation Owner | Define when REVIEW escalates: policy dispute, repeated mismatch, technical failure cluster, or aging breach | Open |
| Manual override path is frozen | Override without a rule creates audit risk | Business Owner + HR / Policy Expert | Confirm who may override and what evidence is mandatory | Open |
| False-positive record path is frozen | Conservative errors must feed rule tuning later | QA + Pilot Operations Support | Record every “should have passed but REVIEWed / rejected” case into risk ledger | Open |
| False-negative record path is frozen | False pass is the highest launch risk | Business Owner + QA | Record every “should have REVIEWed / rejected but passed” case with immediate escalation | Open |
| REVIEW reason taxonomy is frozen | Weekly review becomes noisy if reasons are inconsistent | Product / Process Lead | Use one reason list: title missing, authority suspect, holder mismatch, OCR weak, validation rejected, analyze fail, verify fail | Draft |

Minimum launch rule:
- no pilot launch until REVIEW owner, SLA, escalation path, and override logging rules are all frozen

Suggested operating baseline for kickoff discussion:
- First response SLA: within 2 business hours during pilot hours
- Same-day closure target: by end of business day unless escalated to policy / tech investigation
- Any suspected false-pass case: escalate immediately, do not wait for weekly review

---

## 3. Operating cadence and governance

| Item | Why it matters | Owner | Required action | Status |
|---|---|---|---|---|
| Weekly review cadence is booked | A frozen cadence is required for pilot discipline | Weekly Review Owner | Send recurring invite, set agenda owner, confirm participants | Open |
| Metrics refresh cadence is frozen | Without cadence, metrics become retrospective storytelling | Metrics Owner | Freeze daily collection cut-off and weekly summary deadline | Draft |
| Risk escalation path is frozen | Teams need to know who makes pause / rollback decisions | Business Owner + Product / Process Lead | Define incident severity levels and escalation target | Open |
| Issue ledger maintenance owner is frozen | Unowned issues disappear between meetings | Pilot Operations Support | Maintain single source of truth for pilot issues and actions | Open |
| Launch-week daily check-in is scheduled | First week needs tighter operating rhythm than steady state | Pilot Operations Support | Schedule 10-15 minute daily standup for launch week | Open |
| Weekly report format is frozen | Management needs comparable weekly snapshots | Product / Process Lead | Reuse one reporting template and one evidence source | Draft |

Recommended cadence:
- Launch week: daily ops review before 18:00 CST if pilot traffic exists
- Steady pilot: weekly review every Wednesday 16:00 CST
- Immediate escalation: any severe false-pass, verify-fail spike, request tracing failure, or fallback breakdown

---

## 4. Fallback and manual safety net

| Failure mode | Operational meaning | Owner | Required action | Status |
|---|---|---|---|---|
| Backend unavailable | Verification assistance is temporarily unusable | Backend Engineer + Pilot Ops Support | Announce incident, switch affected cases to manual approval handling, preserve request evidence if available | Draft |
| OCR failure / unreadable image | System cannot safely extract minimum decision evidence | Approver + REVIEW Owner | Route to manual review, request clearer image if policy allows, log as OCR fail | Draft |
| Analyze fail | Upstream recognition step failed; analysis result cannot be trusted | Approver + Pilot Ops Support | Do not infer from prior state, route to manual handling, log incident with request_id if present | Draft |
| Verify fail | Business verification step failed even if analysis succeeded | Approver + Pilot Ops Support | Treat old result as reference only, do not approve from stale result, route to manual handling | Draft |
| Old result visible after retry failure | Current screen may not represent current case state | Frontend Engineer + Approver | Must visibly mark stale state as reference only; approver must not use it as final basis | Draft |
| Non-image upload / wrong file type | Request is outside supported pilot contract | Approver + Product / Process Lead | Block pilot-assisted flow, request valid image upload, record if user training gap is frequent | Draft |
| Human manual fallback | Core safety mechanism, not exception | Business Owner + REVIEW Owner | Pilot continues manually when the system is uncertain, failed, or not trusted | Draft |

Manual fallback rule:
- when in doubt, continue the business process manually and record why the pilot did not provide a final assistive result

---

## 5. Pre-launch verification checklist

| Check item | Required evidence | Owner | Status |
|---|---|---|---|
| real mode is the default operating mode | UI / config evidence and last integration note | Frontend Engineer | Done |
| SICK regression baseline has been rerun | pytest / regression evidence | QA | Done |
| MARRIAGE gating is enabled | merged code + passing targeted tests | Backend Engineer | Done |
| MARRIAGE dataset skeleton exists | checked-in baseline under `datasets/marriage/` | QA | Done |
| targeted regression baseline has been rerun after latest gating change | `tests/test_attachment_verification.py` + `tests/test_marriage_certificate_parser.py` | QA | Done |
| non-image upload behavior has been explicitly validated | test evidence or written launch blocker | QA + Frontend Engineer | Open |
| failure-state checklist has been validated end to end | screenshots / notes for analyze fail, verify fail, OCR weak, stale result, backend unavailable | QA | Open |
| REVIEW SOP is frozen and approved | `docs/review-sop.md` sign-off in kickoff | Product / Process Lead + HR / Policy Expert | Draft |
| metrics schema and risk ledger fields are frozen | `docs/pilot-metrics.md` sign-off | Metrics Owner | Draft |
| pilot roster and launch window are frozen | kickoff roster + calendar invite | Business Owner | Open |
| request_id tracing is operational in real pilot path | traced case evidence from UI to logs | Backend Engineer + QA | Open |

Pre-launch decision:
- current state is not launch-ready until the roster, request tracing, non-image validation, and failure-state checklist are all closed

---

## 6. Kickoff meeting agenda

### Attendees
- Business Owner
- HR / Policy Expert
- Product / Process Lead
- Backend Engineer
- Frontend Engineer
- QA
- Pilot Operations Support
- Pilot Approver representatives

### Agenda
1. confirm pilot scope: SICK + MARRIAGE, single image, approval assistance only
2. confirm real approver roster and launch window
3. confirm REVIEW owner, escalation owner, metrics owner, weekly review owner
4. walk through REVIEW SOP with 3 example cases
5. walk through fallback handling for analyze fail / verify fail / OCR fail / backend unavailable
6. confirm request_id trace path and evidence retention rule
7. confirm metrics fields, reporting cadence, and issue ledger owner
8. make go / no-go decision for limited pilot exposure

### Kickoff outputs
- frozen pilot roster
- frozen launch window
- frozen REVIEW path and SLA
- frozen weekly review meeting
- frozen metrics and risk ledger format
- open blockers list with owner and due date

---

## 7. Immediate open blockers

These are the most likely launch blockers based on current repo state and prior readiness notes:

1. real pilot approver roster is still not frozen by name
2. request_id operational tracing in the real caller path still needs explicit evidence
3. non-image upload / full failure-state checklist has not yet been explicitly signed off for launch
4. weekly review invite, metrics owner, and issue-ledger operator still need real names

Until these four items are closed, treat the project as “ready for launch preparation”, not yet “safe to start pilot traffic”.
