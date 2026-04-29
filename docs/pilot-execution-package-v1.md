# Approval Verification Pilot Execution Package v1

> Document layer: execution edition (detailed project推进版). For decision-oriented reading, start with `docs/01-executive/pilot-summary-v1.md`.

## Background

`id-doc-ocr` has moved beyond a pure OCR capability demo and now has a usable approval-verification chain for leave-attachment scenarios:

- `POST /analyze-document`
- `POST /verify-attachment`
- approval verification UI with three-column layout
- mock mode and real adapter mode
- visible error, fallback, mismatch, and manual-review states

The current need is no longer feature ideation. It is to package the existing capability into a controllable enterprise pilot plan for business owners and HR managers.

This document consolidates the current pilot planning content into a single execution package so the team can launch a small, governed pilot without fragmenting planning across multiple files.

## Goal

Launch a small-scope pilot for leave-attachment verification that:

1. improves approval efficiency,
2. improves consistency of attachment checking,
3. keeps human approvers as the final decision makers,
4. measures value with explicit metrics,
5. remains easy to pause or roll back if risk rises.

## Scope

### In Scope

- Pilot scenarios:
  - SICK leave attachments
  - MARRIAGE leave attachments
- Single attachment, single image only
- Small user group in one business department
- Approval-assistance only
- UI display of:
  - analysis result
  - verification result
  - PASS / REVIEW / REJECT
  - rule results
  - warnings
  - manual review guidance
  - error / fallback / old-result states
- Weekly operational reporting
- Explicit rollback mechanism

### Out of Scope

- Automatic approval or automatic rejection
- PDF and multi-page attachments
- Multi-attachment aggregation logic
- Batch processing
- Broad company-wide rollout
- New attachment categories beyond current pilot focus
- Parser expansion outside pilot priorities

## Time Plan

### Overall Pilot Window

- Week 0: pilot preparation and scope freeze
- Week 1: integration and sandbox validation
- Week 2: limited gray rollout
- Week 3: stable observation and issue closure
- Week 4: pilot evaluation and go/no-go decision

### Week-by-Week Plan

| Week | Weekly Goal | Key Tasks | Owner | Deliverables | Acceptance Standard |
|---|---|---|---|---|---|
| Week 0 | Freeze pilot setup | confirm scope, freeze interface contract, define pilot users, prepare sample pool, confirm rollback rules, align RACI | Product / Process Lead | pilot scope note, interface field list, pilot roster, risk register, RACI | business/HR/product all confirm scope, contract and rollback gates are explicit |
| Week 1 | Complete integration | connect leave system sandbox to verification service, connect UI display, validate error/fallback states, validate logs and request traceability, run integration cases | Backend + Frontend + QA | integration report, UI validation evidence, log samples | sandbox analyze/verify calls succeed, UI can show success/error/fallback states |
| Week 2 | Run gray pilot | expose to small approver group only, keep manual final decision, collect daily REVIEW rate, failures, and mismatch cases, gather first business feedback | Business Owner + Pilot Ops Support | daily reports, issue list, feedback notes | pilot does not block normal approval flow; daily monitoring works |
| Week 3 | Stabilize and observe | monitor case volume and decision distribution, classify misjudgments, analyze high REVIEW or high latency patterns, prepare first metrics baseline | QA + Product / Process Lead | weekly metrics report, misjudgment ledger, exception analysis | measurable trend baseline exists; top issues have root-cause categories |
| Week 4 | Conclude pilot | summarize full-cycle data, evaluate metrics achievement, review risk level, decide expand/continue/pause, produce next-step roadmap | Business Owner + Product / Process Lead | pilot summary report, recommendation memo, next-phase plan | management can make a clear continue/expand/pause decision |

## Owner / Collaboration Roles

### Primary Owner

- Business Owner: final sponsor and decision-maker for starting, shrinking, pausing, or expanding the pilot

### Collaboration Roles

- HR / Policy Expert: confirms policy interpretation, material rules, and misjudgment adjudication
- Product / Process Lead: owns scope, process fit, reporting structure, and pilot coordination
- Backend Engineer: owns API stability, traceability, latency, and service support
- Frontend Engineer: owns approval-page presentation, status communication, and approver usability
- QA: owns sample coverage, integration validation, metrics collection quality, and misjudgment tracking
- Pilot Approvers: use the pilot in real review work and give first-line usability feedback
- Pilot Operations Support: organizes rollout, gathers feedback, drives weekly reporting, tracks actions

### RACI Matrix

| Task | Business Owner | HR / Policy Expert | Product / Process Lead | Backend Engineer | Frontend Engineer | QA | Pilot Approver | Pilot Ops Support |
|---|---|---|---|---|---|---|---|---|
| Confirm pilot scope | A | C | R | I | I | I | I | C |
| Confirm business goal | A | C | R | I | I | I | C | C |
| Freeze interface contract | I | C | A | R | C | C | I | I |
| Design approval flow usage | C | C | A/R | I | C | I | C | C |
| Prepare sample pool | I | A/C | C | I | I | R | I | C |
| Prepare integration environment | I | I | C | A/R | R | C | I | I |
| Validate UI display | I | I | C | C | A/R | C | I | I |
| Logging and traceability | I | I | C | A/R | I | C | I | I |
| Execute integration cases | I | C | C | C | C | A/R | I | I |
| Train / brief pilot approvers | A | C | C | I | I | I | I | R |
| Daily / weekly reporting | I | I | C | C | C | R | I | A/R |
| Misjudgment classification | I | A/C | C | C | I | R | C | C |
| Trigger rollback decision | A | C | R | C | C | C | I | C |
| Final pilot recommendation | A | C | R | C | C | C | C | C |

## Risks

| Risk Area | Description | Business Impact | Control Strategy | Trigger for Escalation |
|---|---|---|---|---|
| Interface failure | analyze/verify timeout or API failure | approver cannot rely on tool | inline error state, old-result marking, revert to manual approval | failure rate > 5% or 30 minutes continuous failure |
| OCR failure | poor image quality or missing key extraction | system cannot support decision | default to REVIEW/manual review for uncertain cases | repeated key-field extraction failures in live cases |
| Misjudgment | PASS given when manual review should have blocked, or overly conservative REVIEW | trust erosion and approval risk | keep human final decision; review every high-impact misjudgment | any serious false-pass case |
| Rule mismatch | business policy nuances not reflected in current rule set | high REVIEW rate or wrong result pattern | HR-led rule review with evidence-based adjustments | repeated same-category rule dispute |
| Latency | slow end-to-end response | approvers stop using the tool | monitor average and P95 latency; keep pilot scope small | P95 continuously above agreed threshold |
| Maintenance overhead | rules, samples, and UI semantics drift apart | pilot becomes expensive to sustain | centralize planning, reporting, and issue classification | weekly closure rate falls behind new issue creation |

## Acceptance Standard

The pilot is considered successful enough to enter the next decision stage only if all of the following hold:

1. It does not block the normal approval process.
2. Manual final decision authority remains intact.
3. Business users can understand PASS / REVIEW / REJECT and manual-review guidance.
4. Error, fallback, and old-result states are clearly visible in the approval UI.
5. Weekly metrics can be produced with stable definitions.
6. Misjudgment cases are traceable and classifiable.
7. Management can make a decision based on measurable evidence rather than anecdotes.

### Suggested Pilot Metrics

| Metric | Definition | Suggested Pilot Target |
|---|---|---|
| Final decision agreement rate | system conclusion vs human final conclusion agreement | >= 85% overall; >= 90% for stable SICK cases |
| REVIEW rate | REVIEW cases / total processed cases | target operating band: 20% ~ 45% |
| API success rate | successful analyze + verify calls / total calls | >= 95% |
| analyze P95 latency | P95 latency for analyze endpoint | < 5s |
| verify P95 latency | P95 latency for verify endpoint | < 3s |
| end-to-end P95 latency | user trigger to visible result | < 8s |
| manual effort reduction | average review time saved per case | >= 30% reduction in target scenario |
| business satisfaction | approver and business owner feedback score | >= 4.0 / 5 |

## Next Action Items

1. Freeze pilot department, user list, and scenario scope.
2. Freeze leave-system integration contract for pilot inputs/outputs.
3. Prepare and label the real pilot sample pool.
4. Schedule the kickoff meeting with business, HR, product, engineering, QA, and pilot approvers.
5. Start Week 0 execution using the weekly plan in this document.

---

# Part A — Pilot Implementation Plan

## Pilot Target Object

### Recommended Pilot Entry Point

- one leave-approval system sandbox or test environment
- one business department
- one small set of approvers
- two attachment scenarios only:
  - SICK
  - MARRIAGE

### Operating Principle

This pilot is an approval-assistance capability.

It is not an automatic approval engine.

The system provides:
- analysis result,
- verification result,
- rule evidence,
- warning signals,
- manual-review suggestion.

The human approver still makes the final approval decision.

## Pilot Rollout Steps

| Step | Activity | Output | Gate |
|---|---|---|---|
| 1 | freeze scope, contract, users, rollback gates | signed-off pilot scope pack | no unresolved scope drift |
| 2 | connect sandbox systems | integration-ready environment | test calls succeed |
| 3 | validate UI states | screenshots / test evidence | success, error, fallback visible |
| 4 | gray release to small approver group | rollout note | no process-blocking issue |
| 5 | daily monitoring and issue classification | daily report | metrics available daily |
| 6 | weekly review and controlled correction | weekly report | no uncontrolled rule drift |
| 7 | final decision review | management recommendation | data-backed go/no-go |

---

# Part B — Weekly Reporting Package

## Weekly Report Template

### Basic Information

| Item | Content |
|---|---|
| Reporting period |  |
| Pilot scope |  |
| Operating phase | integration / gray / observation |
| Weekly one-line conclusion |  |

### Operating Metrics

| Metric | This Week | Notes |
|---|---|---|
| Total processed cases |  |  |
| SICK cases |  |  |
| MARRIAGE cases |  |  |
| PASS count |  |  |
| REVIEW count |  |  |
| REJECT count |  |  |
| PASS ratio |  |  |
| REVIEW ratio |  |  |
| REJECT ratio |  |  |
| Total API calls |  | analyze + verify |
| API success rate |  |  |
| analyze average latency |  | seconds |
| analyze P95 latency |  | seconds |
| verify average latency |  | seconds |
| verify P95 latency |  | seconds |
| end-to-end average latency |  | seconds |
| end-to-end P95 latency |  | seconds |
| OCR failure count |  |  |
| fallback usage count |  |  |
| manual review case count |  |  |

### Misjudgment Cases

| Case ID | Attachment Type | System Result | Human Result | Issue Type | Severity | Root Cause | Action |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

### Business Feedback

| Feedback Source | Scenario | Feedback | Impact | Suggested Action |
|---|---|---|---|---|
|  |  |  |  |  |

### Risks and Blockers

| Risk / Blocker | Severity | Current Status | Description | Owner | Due Date |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Next-Week Plan

| Task | Owner | Target Date | Completion Standard |
|---|---|---|---|
|  |  |  |  |

### Weekly Decision

| Item | Decision |
|---|---|
| Continue gray pilot? |  |
| Expand scope? |  |
| Shrink scope? |  |
| Trigger rollback? |  |
| Final recommendation | continue / shrink / pause / observe |
| Evidence summary | list 1-3 data-backed reasons |

---

# Part C — Pilot Kickoff Meeting Package

## Kickoff Meeting Goal

Use the kickoff meeting to complete five things:

1. align on pilot positioning,
2. freeze pilot scope and business boundaries,
3. confirm human fallback and rollback rules,
4. confirm weekly operating and reporting method,
5. lock owners and deadlines.

## Recommended Attendees

- Business Owner
- HR / Policy Expert
- Product / Process Lead
- Backend Engineer representative
- Frontend Engineer representative
- QA representative
- Pilot Operations Support
- 1~2 pilot approver representatives

## Kickoff Agenda

| Agenda Item | Suggested Time | Objective |
|---|---:|---|
| Background and goal | 5 min | why this pilot exists |
| Current capability and pilot positioning | 10 min | clarify approval-assistance role |
| Pilot scope and boundaries | 10 min | freeze what is in and out |
| Approval flow and human fallback | 10 min | confirm operational safety |
| Timeline and responsibilities | 10 min | confirm who does what |
| Acceptance metrics and rollback gates | 10 min | define success and stop conditions |
| Business questions requiring confirmation | 15 min | lock policy and usage decisions |
| Decisions and next actions | 10 min | create executable action list |

## Questions Business Must Confirm

| Area | Confirmation Question |
|---|---|
| Scope | Is the pilot limited to SICK and MARRIAGE only? |
| Scope | Is the pilot limited to single-image attachments only? |
| Scope | Is PDF and multi-attachment explicitly excluded? |
| Business semantics | What do PASS / REVIEW / REJECT mean in business handling terms? |
| Business semantics | Does REVIEW always go to manual review? |
| Business semantics | Should missing key fields default to REVIEW rather than PASS? |
| Human fallback | Does human approval remain final during the pilot? |
| Human fallback | If the interface fails, do we default back to manual approval? |
| Rule policy | Which fields are mandatory for SICK? |
| Rule policy | Which fields are mandatory for MARRIAGE? |
| Governance | Who signs off rule interpretation disputes? |
| Operations | Which approvers participate in the pilot? |
| Governance | Who receives weekly reporting and makes expand/pause decisions? |

## Kickoff Deliverables

| Deliverable | Description | Owner |
|---|---|---|
| Pilot scope confirmation | final in/out statement | Product / Process Lead |
| Business semantics note | agreed meaning of PASS / REVIEW / REJECT | Business Owner |
| Rule confirmation list | critical policy points approved by HR | HR / Policy Expert |
| RACI sheet | responsibilities and decision rights | Product / Process Lead |
| Week 0 action list | post-meeting execution list with due dates | Pilot Ops Support |
| Rollback gate note | confirmed stop/pause conditions | Business Owner |

---

# Part D — Management Briefing PPT Structure

This structure is designed for business owners and HR managers, not for a technical architecture review.

## Slide 1 — Why this pilot exists

- Core message: attachment checking is currently labor-intensive and inconsistent.
- Suggested content: current approval flow with manual checking highlighted.

## Slide 2 — Current business pain points

- Core message: manual review cost is high, experience varies by approver, and risk handling is inconsistent.
- Suggested content: pain-point list or current-state workflow.

## Slide 3 — What this pilot does

- Core message: the system assists approval by analyzing attachments and presenting PASS / REVIEW / REJECT guidance.
- Suggested content: simple “system assist + human final decision” diagram.

## Slide 4 — What this pilot does not do

- Core message: this is not automatic approval, not full replacement, and not a broad rollout.
- Suggested content: in-scope / out-of-scope table.

## Slide 5 — Why the business should care

- Core message: the pilot aims to save review time, improve consistency, and create traceable evidence.
- Suggested content: before/after comparison or value bullets.

## Slide 6 — What approvers will see

- Core message: the UI already presents decision guidance, rule details, warnings, and manual-review cues clearly.
- Suggested content: page screenshots for PASS and REVIEW scenarios.

## Slide 7 — Risk is controlled

- Core message: scope is small, human fallback is retained, and rollback is explicit.
- Suggested content: three-layer safety diagram: error state -> manual review -> rollback.

## Slide 8 — How the pilot will run

- Core message: 4-week phased pilot with integration, gray rollout, observation, and evaluation.
- Suggested content: pilot timeline.

## Slide 9 — How success will be measured

- Core message: decision quality, REVIEW rate, latency, time saving, and business satisfaction will be measured explicitly.
- Suggested content: KPI table or scorecard.

## Slide 10 — Decision request

- Core message: approve a small, controlled pilot under explicit business and HR governance.
- Suggested content: decision checklist: scope, users, timing, governance, rollback rights.

## Management Presentation Principles

- Use business language, not technical design language.
- Repeat the phrase: “approval assistance, not automatic approval replacement.”
- Emphasize small scope, human fallback, explicit rollback, and measurable value.
- Avoid discussing OCR backend details unless specifically asked.

## Next-Step Action Items

1. Review this package with the product owner and business owner.
2. Use Part C to prepare the kickoff meeting deck and questions list.
3. Use Part D to prepare the management briefing PPT.
4. Keep future pilot-planning revisions versioned under `docs/` rather than creating scattered ad-hoc notes.
5. If the pilot scope changes materially, create `docs/pilot-execution-package-v2.md` rather than overwriting governance history.
