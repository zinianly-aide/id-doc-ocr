# Pilot Launch Readiness v1

## Status
- Stage: `Pilot Launch Readiness`
- Scenario scope: `SICK only`
- Purpose: convert the current verified capability into a minimum operating baseline for a small-scope pilot launch
- Constraint: no new algorithm scope, no contract change, no document-type expansion

## 1. Background

The project has already finished the minimum technical and sample-side closure needed before pilot-operation preparation:

- `docs/contract-pilot-v1.md` is confirmed and remains frozen for this stage
- SICK PASS gating has already been implemented and validated
- the approval verification UI can already express PASS / REVIEW / REJECT, mismatch, error, fallback, and manual-review states
- the SICK sample registry has already reached the minimum three-bucket baseline

This stage is not for new capability work.

This stage is for turning the current SICK verification ability into a pilot-launchable operating package with frozen scope, stable handling rules, metrics, risk controls, request tracing, and a launch checklist.

---

## A. 当前 readiness 状态总结

### A1. Confirmed items

1. Contract status
- `docs/contract-pilot-v1.md` is already confirmed
- no contract change is introduced in this stage

2. SICK gating status
- SICK PASS gating is already上线并验证
- current goal is operationalization, not further rule tuning

3. Sample structure status
- Normal / Abnormal / Edge structure is already达标
- current repo baseline:
  - Normal = 11
  - Abnormal = 10
  - Edge = 6
  - total = 27
  - verified = 25
  - real-source ratio = 48.1%

4. UI / API status
- `/analyze-document` and `/verify-attachment` can be used in real integration verification
- approval UI can already show verification-first semantics and manual-review guidance

### A2. Current readiness conclusion

The project is already past “technical MVP closure” and “sample baseline closure”.

The remaining work before controlled pilot launch is operational readiness:
- freeze the pilot scope
- define measurable launch metrics
- define risk ownership and rollback gates
- define request tracing
- define an approver-operable checklist and fallback SOP

### A3. 当前风险点

1. Real positive samples are still not dominant
- Normal baseline is sufficient for launch preparation, but real or desensitized real positive samples are still limited

2. Metrics are defined but not yet running in live collection
- the team has a measurement definition, but not yet a running pilot data-collection habit

3. request_id is contract-defined but not yet operationalized in the real integration path
- this weakens traceability for incident diagnosis and weekly pilot review

4. Approver roster and pilot window are still placeholders
- the operating package is ready to define the process, but the real pilot user list still needs business confirmation

5. REVIEW-rate acceptability still needs business confirmation in real traffic
- current regression is acceptable technically, but the business side still needs to validate whether REVIEW volume is operationally acceptable

---

## B. 试点范围冻结

### B1. Frozen pilot scope

The pilot launch scope is frozen as follows:

- leave scenario: `SICK` only
- attachment expectation: `MEDICAL_CERTIFICATE`
- attachment count: single attachment only
- file form: single image only
- decision mode: approval assistance only
- final authority: human approver retains final decision
- user scope: small group of pilot approvers (`TBD by business owner / HR`)

### B2. Explicit non-scope for this pilot

The following are explicitly out of scope and must not be added during this launch-readiness stage:

- `MARRIAGE`
- PDF
- multi-attachment
- batch verification
- automatic approval
- automatic rejection
- broader medical-document taxonomy expansion
- OCR model optimization
- new rule design
- contract changes

### B3. Scope-control rule

If a requested change would alter any of the following, it is out of scope for P3 and must not block the pilot-readiness closure:

- contract field definition
- verification rule logic
- supported leave types
- supported file formats
- supported attachment count

---

## C. 试点运行方式

### C1. Approver operating principle

The approver must treat the system as approval assistance only.

Operating order:
1. read `verify_status`
2. read `summary_message`
3. inspect warnings and rule results if needed
4. decide business action according to the frozen pilot SOP
5. retain final human judgment for every case

### C2. PASS / REVIEW / REJECT 的实际审批动作

#### PASS
Operational meaning:
- the system sees no blocking issue under the current frozen SICK pilot baseline

Approver action:
- continue normal approval review
- no extra attachment re-check is required by default
- the approver may still manually inspect if the case is sensitive or context is unusual

#### REVIEW
Operational meaning:
- the system does not conclude outright invalidity, but the case is not safe for direct pass-through

Approver action:
- must enter manual review
- manually inspect applicant identity consistency, leave dates, and attachment quality
- review warnings and rule results before deciding approve / reject / request correction
- do not treat REVIEW as approval-ready

#### REJECT
Operational meaning:
- the current attachment is not acceptable under the frozen pilot baseline

Approver action:
- reject, return, or request correction according to business process
- the approver still owns the final decision, but REJECT should be treated as a strong stop signal

### C3. fallback 策略

#### Interface failure
If the verification request fails or returns an unusable business result:
- display error clearly
- if an older result is still visible, mark it as reference-only
- do not allow stale output to be treated as the latest result
- route the case to manual handling
- record the incident with `request_id`

#### OCR failure or unreadable attachment
If OCR cannot produce reliable usable fields:
- do not force PASS
- route to manual review
- record as OCR-failure or unreadable-document case in pilot metrics
- retain screenshot / sample reference and `request_id` for later review

#### Business fallback rule
For every technical failure path in the pilot:
- business process continues manually
- the case is counted as pilot traffic, but not as successful automated assistance
- pilot operations support records the case for weekly review

### C4. 人工兜底说明

Human fallback is not an exception path outside the design. It is a required part of the pilot design.

Human fallback is mandatory when any of the following is true:
- `verify_status = REVIEW`
- `verify_status = REJECT`
- verification request fails
- OCR result is unreliable
- stale result is visible after a failed retry
- the approver is uncertain despite system output

---

## D. 指标定义

The operational metric definitions for this pilot are maintained in:
- `docs/METRICS.md`

For launch readiness, the minimum required tracked metrics are:
- success rate
- REVIEW rate
- P95 latency
- manual-review ratio

### D1. Metric usage rule

These metrics are launch-operating metrics, not model-benchmark metrics.

They must be reviewed:
- daily during the first launch window if pilot traffic exists
- weekly in pilot review
- immediately when rollback triggers are hit

---

## E. 风险与回滚

The pilot risk and rollback rules are maintained in:
- `docs/RISKS.md`

The minimum risk-governance set for launch readiness includes:
- false-pass risk
- abnormal REVIEW-rate risk
- interface-failure risk
- explicit rollback trigger conditions

### E1. Pilot rollback principle

If pilot safety or traceability becomes unreliable, the pilot must fall back to manual handling rather than forcing continued assisted verification.

---

## F. request_id 落地方案

### F1. Who generates request_id

Preferred owner:
- the leave-system integration layer or pilot gateway generates `request_id` before calling `/verify-attachment`

Fallback owner:
- if the leave system cannot generate it initially, the integration adapter that bridges the leave flow and verification service must generate it

The verification core service should not be the first owner of pilot trace identity, because pilot tracking needs the identifier before downstream service invocation.

### F2. Required format rule

Recommended pattern:
- `LV-SICK-YYYYMMDD-XXXXXX`

Example:
- `LV-SICK-20260429-000123`

Minimum format requirements:
- globally unique within the pilot window
- generated once per verification request
- visible in UI or issue records when needed
- stable across logs, retries, and weekly incident review

### F3. How request_id is carried through

The request path must carry `request_id` end to end:

1. leave request page or integration trigger creates the request
2. integration layer assigns `request_id`
3. integration layer calls verification service with the request context
4. service response echoes `request_id`
5. frontend UI stores or displays `request_id` in operator-visible trace area if error/review investigation is needed
6. logs, weekly issue tracking, and incident records all use the same `request_id`

### F4. How request_id is used for logs and issue tracking

`request_id` must be the primary join key for:
- integration request log
- verification response log
- frontend error or stale-result event log
- pilot issue tracker / weekly risk review entry
- support-side screenshot or evidence collection

Minimum operational rule:
- every pilot incident record must contain `request_id`
- every rollback-triggering incident must be traceable by `request_id`
- weekly pilot review must summarize top incidents by `request_id`, error class, and business outcome

### F5. request_id launch gate

Do not start the live pilot window until request tracing can satisfy all of the following:
- generate once
- echo back in response
- searchable in logs
- recordable in issue tracking
- usable by pilot operations and engineering during investigation

---

## G. 试点启动前 Checklist

The following checklist must be completed before launch:

1. Confirm `docs/contract-pilot-v1.md` remains the only accepted pilot contract baseline.
2. Confirm pilot scope is frozen to `SICK` only and no MARRIAGE pilot traffic is included.
3. Confirm upload scope is single image and single attachment only.
4. Confirm pilot approver roster is named and owned by business owner / HR.
5. Confirm each pilot approver has received the PASS / REVIEW / REJECT SOP.
6. Confirm manual fallback path is accepted by approvers and operations support.
7. Confirm `request_id` can be generated before verification request dispatch.
8. Confirm `request_id` is echoed back and searchable in logs.
9. Confirm `docs/METRICS.md` is the active metric-definition source and owners know how to record the four required metrics.
10. Confirm `docs/RISKS.md` is the active risk-and-rollback source and owners know the rollback triggers.
11. Confirm at least one end-to-end real-adapter run has been demonstrated for the frozen SICK flow.
12. Confirm Normal / Abnormal / Edge sample counts remain at or above the current minimum baseline.
13. Confirm at least the key verified samples remain reproducible and unchanged.
14. Confirm verification UI still shows error / stale / manual-review semantics correctly.
15. Confirm first-week pilot review owner, schedule, and issue-tracking destination are assigned.

---

## Launch Recommendation

### Readiness view

Current state is sufficient to enter controlled pilot-launch preparation.

### What this document does not claim

This document does not claim:
- company-wide readiness
- zero misjudgment risk
- zero manual-review load
- readiness for MARRIAGE, PDF, or multi-attachment flows

### Controlled launch recommendation

Launch should proceed only as a small-scope, SICK-only, human-supervised pilot after the checklist items above are closed.

---

## H. request_id 验证结果

### H1. 验证环境

- validation service: local FastAPI service with current P3.1 request_id changes
- validation endpoint base: `http://127.0.0.1:8013`
- sample mode: current repo samples
- validation flow: caller-generated `request_id` -> `/analyze-document` -> `/verify-attachment`

### H2. 已验证通过的点

1. 每次请求都有唯一 request_id
- caller used generated IDs in the format `LV-SICK-VAL-xxxxxxxx`
- each case reused one request_id across analyze and verify

2. response 中包含 request_id
- both `/analyze-document` and `/verify-attachment` now echo top-level `request_id`
- response header `X-Request-Id` also returns the same value

3. 日志中可按 request_id 检索
- service logs now emit request-scoped lines for:
  - `analyze_input`
  - `analyze_result`
  - `verify_input`
  - `verify_result`
  - request access log with elapsed time

4. 可串起 input -> analyze -> verify
- validated example request_id: `LV-SICK-LOG-00a7ed11`
- the same request_id was observed in:
  - analyze input log
  - analyze result log
  - verify input log
  - verify result log
  - access logs for both endpoints

### H3. 示例日志证据

Example grep result for one validated request_id:

- `analyze_input request_id=LV-SICK-LOG-00a7ed11 ... filename=diagnosis_generated_001.png plugin=diagnosis_proof`
- `analyze_result request_id=LV-SICK-LOG-00a7ed11 doc_type=diagnosis_proof review_action=reject ...`
- `verify_input request_id=LV-SICK-LOG-00a7ed11 applicant_name=张三 expected_attachment_type=MEDICAL_CERTIFICATE ...`
- `verify_result request_id=LV-SICK-LOG-00a7ed11 ... verify_status=PASS`

### H4. 当前结论

- request_id plumbing is now operationally usable for pre-launch validation
- caller generation works
- analyze and verify can share the same request_id
- response echo works
- log search works

---

## I. Rehearsal 结果

### I1. Rehearsal 范围

A single rehearsal batch was executed on 10 current repo samples:

- PASS path samples: 5 Normal
  - `SICK-N-004`
  - `SICK-N-005`
  - `SICK-N-006`
  - `SICK-N-007`
  - `SICK-N-008`
- manual-review path samples: 5 mixed Abnormal / Edge
  - `SICK-A-005`
  - `SICK-A-006`
  - `SICK-A-009`
  - `SICK-A-010`
  - `SICK-E-005`

Each case followed the same rehearsal sequence:
1. upload sample
2. inspect analysis
3. inspect verification
4. simulate approver action
5. record whether manual review is required

### I2. Rehearsal 执行结果

- total rehearsal flows: 10
- PASS -> approve: 5
- REVIEW -> manual review: 5
- fallback needed because of interface failure: 0

Observed approval actions:
- PASS cases were understandable as “continue normal approval review”
- REVIEW cases were understandable as “must enter manual review”
- date mismatch and applicant mismatch warnings were both understandable by approver-side reading

### I3. 审批人可能困惑的点

1. analysis 结论会比 verification 更严
- in the PASS rehearsal set, analysis frequently showed `review` / `reject` tendency while verification still returned `PASS`
- this confirms the earlier mismatch-risk note is still operationally relevant

2. approver must know which layer is primary
- rehearsal confirms the page must continue to emphasize:
  - verification result is the primary business signal
  - analysis risk is supporting evidence, not the final approval signal

3. REVIEW 的来源需要直接可见
- when REVIEW is triggered by date mismatch or name mismatch, the warning is understandable
- if REVIEW were shown without warning context, approvers would likely hesitate

### I4. PASS / REVIEW 可理解性判断

- PASS 可理解性：Yes
  - current wording is sufficient for a normal approval continuation decision
- REVIEW 可理解性：Yes
  - current warning-driven explanation is sufficient for manual-review entry

### I5. fallback 是否清楚

- Yes, at the SOP level
- in this rehearsal batch there was no interface failure, but the handling rule remained clear:
  - any technical failure -> stale result marked reference-only -> manual handling

### I6. Rehearsal 结论

The approval flow is executable for a controlled pilot rehearsal baseline.

However, the remaining launch blocker is no longer SOP ambiguity.
The remaining blockers are pilot-user assignment, real metric collection continuity, and keeping request_id traceability in the real integrated path.

---

## J. Integration Freeze

### J1. request_id 接入责任边界

Frozen ownership for go-live:

- source owner: leave-system caller or pilot gateway
- generation owner: caller-side integration layer before any verification request is sent
- service responsibility: accept the provided `request_id`, echo it in response, and emit it in logs
- operations responsibility: use the same `request_id` as the primary trace key in incident review and weekly tracking

This means the verification service is not the originator of pilot trace identity in go-live mode.
The request must arrive with a caller-generated `request_id`.

### J2. request_id 格式规范

Frozen format rule:
- `LV-SICK-YYYYMMDD-XXXXXX`

Example:
- `LV-SICK-20260506-000123`

Required properties:
- unique per verification case
- generated once by caller-side integration
- reused across analyze and verify for the same approval case
- searchable in logs and weekly review records

### J3. analyze / verify 接入方式

The frozen request path is:
1. caller or pilot gateway generates `request_id`
2. caller includes `request_id` in `/analyze-document` request payload
3. caller includes the same `request_id` in `/verify-attachment` request payload
4. service echoes `request_id` in response body and `X-Request-Id` response header
5. service logs include the same `request_id` in request access and stage logs

### J4. 日志系统透传方式

The same `request_id` must appear in:
- caller integration request log
- service analyze input/result log
- service verify input/result log
- API access log
- weekly issue tracking entry when incidents occur

### J5. Integration Freeze Checklist

1. Caller-side integration owner is explicitly named before launch.
2. Caller generates `request_id` using the frozen format.
3. The same `request_id` is passed to both analyze and verify.
4. `request_id` is searchable in service logs and issue records.
5. Weekly issue review uses `request_id` as the primary trace key.

---

## K. Metrics Operation

### K1. Operational Ownership

Frozen ownership for the pilot launch window:

- daily recording owner: QA + Pilot Operations Support
- weekly summary owner: Pilot Operations Support
- launch decision / rollback decision owner: Business Owner

Supporting roles:
- Product / Process Lead: checks metric completeness and review readiness
- Backend / Frontend Engineer: supports trace lookup and failure diagnosis

### K2. Operating cadence

Frozen cadence for go-live:

- daily recording: every pilot business day before `18:00 CST`
- weekly review: every Wednesday `16:00 CST`
- weekly reporting source: `docs/WEEKLY-STATUS.md` only

### K3. Weekly review output rule

The only weekly reporting source for pilot operations is:
- `docs/WEEKLY-STATUS.md`

It must contain at minimum:
- success rate snapshot
- REVIEW rate snapshot
- manual review ratio snapshot
- notable incident list by `request_id`
- go / hold / rollback recommendation

---

## L. Pilot Roster & Schedule

### L1. Pilot roster freeze

Frozen pilot roster format for go-live:

- pilot department: `HR Shared Service Center / Leave Approval Team`
- approver roster:
  - Approver A (`HR-Approver-01`)
  - Approver B (`HR-Approver-02`)
  - Backup Approver (`HR-Backup-01`)

This roster format is the launch placeholder baseline and must be replaced by the real named roster before the launch meeting closes.

### L2. Launch window

Frozen proposed launch window:
- pilot start date: `2026-05-06`
- pilot observation window: `2026-05-06` to `2026-05-12`
- first weekly review: `2026-05-13 16:00 CST`

### L3. Fallback / rollback ownership

If pilot safety or operability becomes unacceptable:
- rollback trigger is evaluated using `docs/RISKS.md`
- Pilot Operations Support raises the incident
- Product / Process Lead prepares the summary
- Business Owner makes the final go / hold / rollback decision

---

## M. Go-Live Checklist

Final freeze checklist:

- request_id 已接入：Yes
- 指标采集责任人已确认：Yes
- 周度 review 已排期：Yes
- 审批人名单已确认：No
- fallback 机制已确认：Yes

### M1. Freeze conclusion

The pilot is launch-ready at the process and governance layer except for final confirmation of the real named approver roster.

---

## N. 审批人图文 SOP

本节用于给试点审批人直接上手，不讨论规则实现，只讲“看到什么、怎么操作、怎么判断”。

### N1. 使用前准备

1. 打开审批附件核验页面。
2. 确认当前审批单是 `SICK` 场景。
3. 确认只有单张图片附件进入本次试点范围。
4. 如页面无法加载、接口报错或附件不是单图，直接走人工处理。

### N2. 页面区域说明（先认识页面）

审批人进入页面后，重点只看 4 个区域：

1. 顶部控制区
- 用于切换数据源和演示场景
- 真实试点时，只需要关注当前是否为正式联调模式

2. 附件列表区
- 确认当前核验的是哪一张图片
- 确认当前附件状态是 `PASS` / `REVIEW` / `REJECT`

3. AnalysisPanel
- 这是识别 / 解析 / 质量层建议
- 只能作为辅助判断，不是最终审批信号

4. VerificationPanel
- 这是业务核验结论主区域
- 审批时以这里的 `PASS` / `REVIEW` / `REJECT` 为主

### N3. 图 1：PASS 场景应该怎么看

附图 1：`docs/assets/pilot-sop-pass.png`

阅读顺序：
1. 先看附件列表，确认当前附件和状态。
2. 再看 `VerificationPanel`：
   - 核验状态是否为 `PASS`
   - 风险等级是否为 `LOW`
   - 是否显示“无需人工复核”
3. 如 `PASS` 且无额外 warning：
   - 继续正常审批
   - 无需额外附件复核
4. 如页面同时提示“分析建议与业务核验结论不一致”：
   - 仍以 `VerificationPanel` 业务核验结论为主
   - 左侧 analysis 风险只作为补充参考

PASS 场景审批动作：
- 结论：继续正常审批
- 记录：无需单独升级
- 例外：若审批人主观判断材料异常，仍可转人工复核

### N4. 图 2：REVIEW 场景应该怎么看

附图 2：`docs/assets/pilot-sop-review.png`

阅读顺序：
1. 先看 `VerificationPanel` 是否为 `REVIEW`。
2. 看“人工复核提示”区域。
3. 看 warning / 规则核验明细，确认触发原因。
4. 看“请求侧证据”，确认申请信息与材料信息是否一致。

REVIEW 场景常见触发原因：
- 姓名不一致
- 请假日期与材料日期不一致
- 关系人不一致
- 材料类型虽匹配，但存在业务风险 warning

REVIEW 场景审批动作：
- 必须进入人工复核
- 不得直接放行
- 根据人工复核结果决定：批准 / 驳回 / 退回补充材料

### N5. 审批动作速查表

1. `PASS`
- 代表：业务规则核验通过
- 动作：继续正常审批
- 是否必须人工复核：否

2. `REVIEW`
- 代表：系统无法直接放行
- 动作：进入人工复核
- 是否必须人工复核：是

3. `REJECT`
- 代表：当前材料不满足接收条件
- 动作：驳回、退回或要求补正
- 是否必须人工复核：按业务流程处理，但不得直接通过

### N6. 异常 / fallback SOP

以下情况一律不要依赖系统结论直接审批：

1. 页面报错
2. 接口超时
3. OCR 失败
4. 页面提示当前结果仅供参考 / stale result
5. 附件不是单图或超出试点范围

异常场景动作：
- 第一步：改走人工处理
- 第二步：记录 `request_id`
- 第三步：把问题提交给 Pilot Operations Support
- 第四步：必要时由 Business Owner 决定 go / hold / rollback

### N7. 审批人一句话原则

- 先看右侧 `VerificationPanel`
- 再看 warning 和证据
- `PASS` 才走正常审批
- `REVIEW` 一律进人工复核
- 出错时一律人工兜底
