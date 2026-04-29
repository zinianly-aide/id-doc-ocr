# Pilot Summary v1

## Background

Leave-attachment review in the target approval workflow is still largely manual. Approvers need to inspect the attachment, compare key fields against the leave request, and decide whether the material is acceptable.

The current `id-doc-ocr` project already has a usable pilot baseline:

- attachment analysis via `/analyze-document`
- business verification via `/verify-attachment`
- approval verification UI with clear PASS / REVIEW / REJECT presentation
- visible error, fallback, mismatch, and manual-review states

This creates the right moment to run a small, controlled pilot focused on business value rather than more feature expansion.

## Goal

Run a small-scope pilot that validates whether the current approval-verification capability can:

1. reduce repetitive manual attachment checking,
2. improve approval consistency,
3. provide usable evidence for approvers,
4. stay operationally safe through human fallback and rollback control.

## Current Value

The current solution already provides business-visible value in four areas:

1. Faster first-pass review
- the system can pre-analyze the attachment and surface verification guidance before the approver manually inspects every field.

2. Better review consistency
- PASS / REVIEW / REJECT, rule results, and warning messages provide a more standardized review reference.

3. Clear manual-review guidance
- uncertain or conflicting cases can be directed to REVIEW instead of being silently passed through.

4. Operational transparency
- error states, fallback states, and “old result / reference only” states are already visible in the UI, reducing misuse risk.

## Scope

### In Scope

- pilot business scenarios:
  - SICK leave attachments
  - MARRIAGE leave attachments
- one business department
- a small approver group
- single attachment, single image only
- approval assistance only
- human final decision retained

### Out of Scope

- automatic approval or automatic rejection
- company-wide rollout
- PDF, multi-page, or multi-attachment processing
- new attachment categories beyond current pilot focus
- complex workflow automation beyond the current approval-assistance loop

## Risk Control

The pilot is designed to be operationally safe.

1. Human final decision remains unchanged
- the system does not replace the approver.

2. Small-scope rollout
- only one department and a limited approver group are included initially.

3. Explicit fallback and rollback
- if the interface fails, OCR fails, or results become unreliable, the process falls back to manual approval.

4. Conservative treatment of uncertainty
- uncertain or weakly supported cases are expected to go to REVIEW rather than be auto-treated as safe.

5. Weekly metric review
- success rate, REVIEW rate, latency, and misjudgment cases are reviewed weekly.

## Time Plan

| Phase | Time | Purpose |
|---|---|---|
| Week 0 | preparation | freeze scope, users, contract, rollback gates |
| Week 1 | integration | complete sandbox integration and UI validation |
| Week 2 | gray pilot | expose to a small approver group only |
| Week 3 | observation | monitor live use, classify issues, review metrics |
| Week 4 | evaluation | decide continue / expand / shrink / pause |

## Owner / Collaboration Roles

### Primary Owner

- Business Owner

### Core Collaboration Roles

- HR / Policy Expert
- Product / Process Lead
- Backend Engineer
- Frontend Engineer
- QA
- Pilot Approvers
- Pilot Operations Support

## Risks

| Risk | What it means in business terms | Control |
|---|---|---|
| Interface failure | approvers cannot rely on system output | manual fallback, visible error state |
| OCR failure | key fields are missing or image quality is too poor | route to REVIEW / manual review |
| Misjudgment | wrong PASS or wrong REVIEW/REJECT weakens trust | human final approval retained; weekly case review |
| Rule mismatch | business policy is not fully reflected | HR-led rule confirmation and correction |
| Latency | slow response reduces actual usage | keep pilot scope small and monitor P95 latency |

## Acceptance Standard

The pilot is considered successful enough for expansion discussion only if:

- the normal approval flow is not blocked,
- business users can understand and use the result presentation,
- human final decision remains intact,
- metrics can be reviewed weekly,
- risk cases are identifiable and controllable,
- management can make a data-based expand / continue / pause decision.

## Decision Request

This summary requests management confirmation on the following items:

1. approve a small-scope pilot for SICK and MARRIAGE attachment verification,
2. approve operation in “approval assistance” mode only,
3. approve human final decision retention throughout the pilot,
4. approve a 5-week pilot window from Week 0 to Week 4,
5. approve rollback rights if reliability or trust drops below threshold.

## Next Action Items

1. Confirm pilot department and approver list.
2. Confirm the pilot input/output contract with the leave-approval system.
3. Prepare the kickoff meeting using the pilot kickoff package.
4. Start Week 0 preparation after management approval.
5. Use the execution document for detailed project tracking.
