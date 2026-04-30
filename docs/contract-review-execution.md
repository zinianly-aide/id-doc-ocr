# Contract Review Execution

## Background

`docs/contract-pilot-v1.md` is now in Candidate status. The next objective is not further drafting. The next objective is to execute a disciplined cross-team review and determine whether the contract becomes the formally confirmed pilot contract.

This document is the execution version for the review meeting itself.

## Goal

Run one contract review meeting that:

1. confirms or blocks the current candidate contract,
2. uses the review checklist as the single review path,
3. prevents scope creep during the meeting,
4. produces a clear result: Confirmed / Blocked / Revision.

## Scope

### In Scope
- review the candidate contract as written
- validate field completeness
- validate naming alignment
- validate business semantics
- validate request_id operability
- validate error-handling acceptability
- classify blockers and assign owners

### Out of Scope
- adding new pilot scope
- changing supported scenarios beyond `SICK` and `MARRIAGE`
- discussing PDF / multi-attachment / automatic approval
- redesigning service architecture
- entering P2 readiness work

## Time Plan

| Item | Value |
|---|---|
| Recommended meeting date | 2026-05-05 |
| Recommended meeting duration | 45 minutes |
| Preparation requirement | all participants read `docs/contract-pilot-v1.md` and `docs/contract-review-checklist.md` before the meeting |
| Same-day output | review conclusion + blocker list |

## Owner / Collaboration Roles

### Meeting Owner
- Product / Process Lead

### Required Participants
- Business Owner
- HR / Policy Expert
- Backend Engineer
- Frontend Engineer
- QA
- Pilot Operations Support

### Optional Participant
- Leave-system integration owner

## Meeting Basic Information

| Item | Content |
|---|---|
| Meeting name | Pilot Contract Review v1 |
| Meeting type | Cross-team alignment review |
| Contract under review | `docs/contract-pilot-v1.md` |
| Companion checklist | `docs/contract-review-checklist.md` |
| Blocker ledger | `docs/contract-review-blockers.md` |
| Current contract status | Candidate |

## Meeting Objective

Confirm the current pilot contract.

The meeting must not drift into feature expansion.

The only decision target is:

Can `docs/contract-pilot-v1.md` be treated as the formally confirmed pilot contract for the small-scope pilot?

## Review Process

The meeting should be executed strictly in the following order.

| Step | Review Topic | Source |
|---|---|---|
| 1 | Confirm review rules and out-of-scope boundary | this document |
| 2 | Walk checklist item: 字段是否齐全 | `docs/contract-review-checklist.md` |
| 3 | Walk checklist item: 字段命名是否与假勤系统一致 | checklist |
| 4 | Walk checklist item: 是否存在系统无法提供字段 | checklist |
| 5 | Walk checklist item: PASS / REVIEW / REJECT 语义是否被业务接受 | checklist |
| 6 | Walk checklist item: 错误码是否可处理 | checklist |
| 7 | Walk checklist item: request_id 是否可落地 | checklist |
| 8 | Walk checklist item: 是否存在必须补充字段 | checklist |
| 9 | Walk checklist item: leave_type 使用方式是否接受 | checklist |
| 10 | Walk checklist item: MARRIAGE 关系字段约束是否接受 | checklist |
| 11 | Walk checklist item: 人工兜底机制是否接受 | checklist |
| 12 | Decide meeting result: Confirmed / Blocked / Revision | meeting owner + decision owners |

## Decision Rules

### General Rule

No one expands scope during this meeting.

If a topic requires new scope, it must be logged as a blocker or follow-up item, not folded silently into v1 during the meeting.

### Who decides what

| Topic Type | Final Decision Owner |
|---|---|
| Business action meaning (`PASS` / `REVIEW` / `REJECT`) | Business Owner |
| HR / policy acceptability | HR / Policy Expert |
| Field availability in leave system | Business Owner + Leave-system integration owner |
| request_id operability and integration feasibility | Backend Engineer |
| UI consumption and operational presentation feasibility | Frontend Engineer + Product / Process Lead |
| Testability and observability | QA |
| Final meeting outcome | Product / Process Lead consolidates; Business Owner confirms |

## Output Definition

### 1. Confirmed
Use when:
- no blocking issues remain,
- business and HR accept the status semantics,
- engineering and QA accept feasibility,
- request_id and error handling are operationally acceptable.

Result:
- `docs/contract-pilot-v1.md` can move from Candidate to Confirmed.

### 2. Blocked
Use when:
- one or more high-severity blockers prevent pilot launch readiness,
- the contract cannot be used safely as-is.

Result:
- blockers must be logged in `docs/contract-review-blockers.md`
- owners and due dates must be assigned
- contract remains Candidate

### 3. Revision
Use when:
- the contract is directionally acceptable,
- but one or more non-trivial clarifications are required before confirmation,
- the issue is not broad enough to justify v2 scope expansion.

Result:
- revision items are logged
- contract remains Candidate until the agreed revision is completed and re-reviewed

## Risks

| Risk | Description | Control |
|---|---|---|
| Scope drift | participants use the meeting to request non-pilot expansion | meeting owner enforces out-of-scope rule |
| Unowned decisions | everyone comments but no one decides | use the decision-owner table above |
| Hidden blockers | unresolved issues are mentioned verbally but not tracked | all blockers must enter the blocker ledger |
| Ambiguous outcome | meeting ends without a clear result state | the meeting must end as Confirmed / Blocked / Revision |

## Acceptance Standard

The meeting execution is considered successful only if:

1. the checklist is walked item by item,
2. each issue is either accepted, blocked, or marked for revision,
3. any blocker is logged with owner and due date,
4. the meeting ends with one explicit outcome state,
5. the next governance action is known.

## Next Action Items

1. Schedule the review meeting for 2026-05-05.
2. Share the contract, checklist, and blocker ledger in advance.
3. Run the meeting with the step-by-step review sequence above.
4. Record all blockers immediately in `docs/contract-review-blockers.md`.
5. If no blockers remain, advance contract status to Confirmed in the next update.
