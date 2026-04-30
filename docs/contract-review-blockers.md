# Contract Review Blockers

## Background

The pilot contract review may surface blocking issues that prevent `docs/contract-pilot-v1.md` from becoming the formally confirmed pilot contract.

These issues must not stay in chat history or meeting memory only. They must be recorded in one blocker ledger with ownership and due dates.

## Goal

Track contract-review blockers in one place so the team can:

1. distinguish blocking issues from discussion noise,
2. assign ownership,
3. track due dates,
4. decide when the contract can move from Candidate to Confirmed.

## Scope

### In Scope
- blockers raised during contract review
- blockers by category: field / semantics / system capability / process
- owner, severity, deadline, and current status

### Out of Scope
- non-blocking suggestions
- future-scope ideas
- P2 and later readiness items

## Time Plan

| Step | Purpose |
|---|---|
| During review | log blocker immediately |
| After review | assign owner and due date |
| Before reconfirmation | verify closure status |

## Owner / Collaboration Roles

### Primary Owner
- Product / Process Lead

### Collaboration Roles
- Business Owner
- HR / Policy Expert
- Backend Engineer
- Frontend Engineer
- QA
- Pilot Operations Support

## Blocker Ledger

本轮 contract review 结论：当前 checklist 未发现 blocker，台账暂为空。

| blocker_id | 类别 | 描述 | 提出方 | 影响范围 | 严重级别 | 处理方式 | Owner | 截止时间 | 状态 |
|---|---|---|---|---|---|---|---|---|---|

## Category Definitions

| 类别 | Meaning |
|---|---|
| 字段 | field presence, field naming, field value expectation |
| 语义 | PASS / REVIEW / REJECT or business-action meaning |
| 系统能力 | service, leave system, integration, request_id, error handling feasibility |
| 流程 | approval flow, manual fallback, operational handling |

## Status Definitions

| 状态 | Meaning |
|---|---|
| Open | blocker exists and is not yet resolved |
| Resolved | blocker has been closed and no longer prevents confirmation |

## Risk

| Risk | Description | Control |
|---|---|---|
| Missing blocker trace | meeting raises issues but nothing is logged | use this file live during review |
| Owner ambiguity | blocker exists but nobody owns it | every blocker must have one named owner |
| Deadline drift | blocker resolution has no timeline | every blocker must have due date |
| False closure | blocker is considered solved without explicit confirmation | only mark Resolved when the review owner confirms |

## Acceptance Standard

This blocker ledger is working correctly only if:

1. every blocking issue from the review meeting is logged here,
2. each blocker has category, owner, due date, and status,
3. the contract cannot move to Confirmed while unresolved High blockers remain,
4. the team can use this file to drive reconfirmation.

## Next Action Items

1. Use this file live during the contract review meeting.
2. Log every blocking issue immediately when raised.
3. After the meeting, assign owner and due date for each open blocker.
4. Re-check this ledger before any status change from Candidate to Confirmed.
