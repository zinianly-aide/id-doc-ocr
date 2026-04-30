# Contract Review Checklist

## Background

`docs/contract-pilot-v1.md` has been produced as the pilot integration contract baseline. Before the project can treat it as the formally frozen pilot contract, cross-team review is required.

This checklist is used to confirm that the current contract is complete, operable, and acceptable for the pilot.

## Goal

Provide one review checklist for business, HR, product, engineering, QA, and pilot operations so the team can determine whether `docs/contract-pilot-v1.md` can move from candidate status to formally confirmed pilot contract status.

## Scope

### In Scope
- field completeness review
- field naming alignment review
- system capability alignment review
- status semantics acceptance review
- error handling acceptance review
- request traceability review
- missing-field identification

### Out of Scope
- adding new pilot scope beyond v1
- changing business scenarios beyond `SICK` and `MARRIAGE`
- expanding to PDF, multi-attachment, or automatic approval
- implementation change requests not directly required for contract confirmation

## Time Plan

| Step | Purpose | Target |
|---|---|---|
| Review preparation | distribute candidate contract and checklist | immediately |
| Cross-team review meeting | confirm checklist items | next contract review meeting |
| Review conclusion | mark accepted / pending / blocked items | same day as review |

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

## Review Checklist

| Check Item | Review Question | Owner | Status | Notes |
|---|---|---|---|---|
| 字段是否齐全 | Are all required pilot integration fields present in the contract? | Product / Process Lead | Pending |  |
| 字段命名是否与假勤系统一致 | Do field names match the leave-system naming that will actually be used in integration? | Business Owner / Product / Backend | Pending |  |
| 是否存在系统无法提供字段 | Does the current leave system have any field in the contract that it cannot currently provide? | Business Owner / Backend | Pending |  |
| PASS / REVIEW / REJECT 语义是否被业务接受 | Does the business agree with the frozen meaning and suggested business action for all three statuses? | Business Owner / HR | Pending |  |
| 错误码是否可处理 | Can the leave system, operations process, and approvers handle the listed normalized error codes? | Product / Backend / QA | Pending |  |
| request_id 是否可落地 | Can request_id be generated, carried through integration, echoed back, and used in issue tracking? | Backend / QA | Pending |  |
| 是否存在必须补充字段 | Is there any field that is absolutely required for pilot launch but currently missing from the contract? | All reviewers | Pending |  |
| leave_type 使用方式是否接受 | Is `leave_type` acceptable as the mandatory pilot scenario selector for v1? | Business Owner / Product | Pending |  |
| MARRIAGE 关系字段约束是否接受 | Are `related_person_name` and `related_person_relation=spouse` acceptable mandatory assumptions for the marriage pilot? | HR / Business Owner | Pending |  |
| 人工兜底机制是否接受 | Is the defined manual fallback rule acceptable for the pilot operating mode? | Business Owner / HR / Ops | Pending |  |

## Review Conclusion Template

| Conclusion Item | Result |
|---|---|
| Contract accepted as-is | Yes |
| Accepted with non-blocking notes | No |
| Blocking issue exists | No |
| Requires v1 clarification only | No |
| Requires v2 change | No |

## Risks

| Risk | Description | Control |
|---|---|---|
| Silent disagreement | Teams assume different meanings for the same field or status | use this checklist as the single review sheet |
| Capability mismatch | contract field exists but leave system or service cannot support it operationally | explicit “system can/cannot provide” check |
| Trace failure | request_id agreed conceptually but not implemented in real flow | force dedicated request_id review item |
| Scope creep in review | teams use review to add new pilot features | keep review limited to v1 alignment only |

## Acceptance Standard

The contract review is considered complete only if:

1. every checklist row has a clear conclusion,
2. blocking issues are explicitly separated from non-blocking notes,
3. business and HR accept the status semantics,
4. engineering and QA accept traceability and error handling assumptions,
5. the team can state whether `docs/contract-pilot-v1.md` is formally confirmed or still pending.

## Next Action Items

1. Send `docs/contract-pilot-v1.md` and this checklist to all review participants.
2. Hold the cross-team contract alignment meeting.
3. Record accepted items, blockers, and follow-up actions in this checklist or meeting notes.
4. If no blocking issues remain, mark the pilot contract as formally confirmed.
