# Contract Review Meeting

## Background

The pilot contract has been written as `docs/contract-pilot-v1.md`. The current stage is no longer contract drafting. The current stage is cross-team alignment to determine whether the v1 contract can be treated as the formal pilot contract.

## Goal

Use one short review meeting to confirm whether `docs/contract-pilot-v1.md` is acceptable for pilot launch preparation.

The meeting should answer one core question:

Can the team treat the current v1 contract as the single approved contract for pilot integration?

## Scope

### In Scope
- confirm request-field acceptability
- confirm response-field acceptability
- confirm business status semantics
- confirm error handling acceptability
- confirm request traceability expectation
- identify whether any missing field is truly blocking

### Out of Scope
- feature expansion
- PDF or multi-attachment support
- deep technical redesign
- non-pilot scenario expansion

## Time Plan

| Item | Suggested Time |
|---|---:|
| Meeting length | 30–45 min |
| Preparation | before meeting: read contract and checklist |
| Output confirmation | same day |

## Owner / Collaboration Roles

### Primary Owner
- Product / Process Lead

### Required Participants
- Business Owner
- HR / Policy Expert
- Backend Engineer
- Frontend Engineer
- QA
- Pilot Operations Support

## 本次 review 目标

1. confirm whether the current pilot field set is sufficient,
2. confirm whether business semantics are acceptable,
3. confirm whether request_id can be operationalized,
4. confirm whether current error-code design is usable,
5. conclude whether the contract becomes formally confirmed or remains pending.

## Contract 关键点

1. v1 scope is only `SICK` and `MARRIAGE`
2. v1 supports only single-image, single-attachment verification
3. the pilot is approval assistance only, not automatic approval
4. `leave_type` is treated as mandatory pilot business input
5. response must expose stable approval-facing outputs
6. `PASS` / `REVIEW` / `REJECT` are business workflow signals, not just technical statuses
7. `request_id` is mandatory for pilot traceability
8. technical failures must route to manual fallback

## 需要业务确认的问题（10条以内）

1. 当前 `leave_type`、`applicant_name`、日期字段、关系字段是否与假勤系统实际字段一致？
2. 对 `SICK` 和 `MARRIAGE` 这两个场景，v1 范围是否可以接受？
3. `PASS` 是否可被定义为“无需额外材料复核，审批人可继续正常审批判断”？
4. `REVIEW` 是否可被定义为“必须进入人工复核，不得视为通过”？
5. `REJECT` 是否可被定义为“材料当前不可接受，应退回或要求补充/更正”？
6. 假勤系统是否能稳定提供 `related_person_name` 与 `related_person_relation`（婚假场景）？
7. 当前错误码集合是否足以支撑审批流程中的异常处理与运营跟踪？
8. `request_id` 是否能由假勤系统或集成层稳定生成并贯穿全链路？
9. 当前 contract 中是否存在业务上必须补充、否则不能启动试点的字段？
10. 若本次 review 无阻塞问题，是否同意将 v1 contract 作为试点正式确认版使用？

## 风险

| Risk | Description | Control |
|---|---|---|
| Review drifts into redesign | meeting becomes a feature discussion instead of an alignment decision | keep agenda limited to v1 confirmation |
| Business semantics remain fuzzy | PASS / REVIEW / REJECT are not truly accepted | explicitly ask for yes/no acceptance |
| Missing-field ambiguity | teams say “maybe later” instead of deciding if a field is blocking | force blocking/non-blocking classification |

## 验收标准

The meeting is considered successful only if:

1. the 10 confirmation questions are answered,
2. any missing fields are classified as blocking or non-blocking,
3. request_id operability is explicitly decided,
4. a clear contract decision is made:
   - formally confirmed, or
   - pending with blockers.

## 下一步行动项

1. Run the meeting with the required participants.
2. Fill in `docs/contract-review-checklist.md` during or immediately after the meeting.
3. If blocked, record the blocker list and owner.
4. If accepted, update the contract status from Candidate to Confirmed in the next governance action.
