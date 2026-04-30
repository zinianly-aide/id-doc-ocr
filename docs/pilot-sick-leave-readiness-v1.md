# Sick Leave Pilot Readiness v1

## Background

The project has already completed the pilot contract baseline and approval-verification product baseline:

- `docs/contract-pilot-v1.md` is Confirmed
- `/analyze-document` and `/verify-attachment` are available
- the approval verification UI can display success, mismatch, error, fallback, and manual-review states

The next step is not wider feature expansion. The next step is to make the SICK leave scenario the first pilot-ready operating baseline.

SICK is chosen first because it is currently the closest scenario to stable pilot use.

## Goal

Define the minimum operational baseline required to run a small-scope SICK leave pilot safely.

This document freezes:

1. the sample-system expectation,
2. the pilot metric baseline definition,
3. the approval-side operating SOP,
4. the current risk boundary,
5. the acceptance standard for entering pilot.

## Scope

### In Scope
- `leave_type=SICK`
- single attachment
- single image
- attachment type expectation: `MEDICAL_CERTIFICATE`
- approval assistance only
- manual final decision retained
- metric baseline for pilot observation

### Out of Scope
- `MARRIAGE`
- PDF
- multi-attachment
- automatic approval
- broader medical-document taxonomy expansion
- non-pilot OCR optimization work

## Time Plan

| Phase | Purpose | Output |
|---|---|---|
| Current phase | define pilot-ready baseline for SICK | this document |
| Next phase | prepare sample pool and operational metric tracking | sample register + metrics docs |
| Pilot phase | run controlled SICK pilot with frozen baseline | measurable pilot data |

## Owner / Collaboration Roles

### Primary Owner
- Product / Process Lead

### Core Collaboration Roles
- Business Owner
- HR / Policy Expert
- Backend Engineer
- Frontend Engineer
- QA
- Pilot Operations Support
- Pilot Approvers

## A. 样本体系

The SICK pilot sample system should be grouped by operational quality, not just by file source.

### 1. 正常样本（清晰 / 标准）

Purpose:
- validate the standard successful path
- confirm expected PASS or low-friction REVIEW behavior
- build the first stable baseline

Sample characteristics:
- clear image
- readable patient name
- readable rest dates
- readable issue date
- no obvious cropping loss
- low glare / low blur

Suggested sample classes:
- standard diagnosis certificate image
- standard medical proof image with complete dates
- standard clear image where `patient_name == applicant_name`

Minimum expectation for pilot preparation:
- at least 10 usable normal samples
- at least 3 different layout / format variants if available

### 2. 异常样本（字段缺失 / 模糊 / 遮挡）

Purpose:
- validate that the system does not over-release risky material
- ensure weak cases route to REVIEW or manual fallback

Sample characteristics:
- missing patient name
- missing rest start / end date
- missing issue date
- obvious blur
- glare over key field area
- partial crop or field occlusion
- image quality still uploadable but operationally weak

Suggested sample classes:
- name missing or unreadable
- date field partially unreadable
- hospital/seal area missing
- blurry mobile photo
- cropped image with missing lower section

Minimum expectation for pilot preparation:
- at least 8 abnormal samples
- each major abnormal mode should have at least 1 example

### 3. 边界样本（OCR弱、日期模糊等）

Purpose:
- validate borderline review behavior
- distinguish between clean PASS path and “needs human check” path

Sample characteristics:
- OCR can partially read fields but with weak confidence
- dates readable by human but not stably machine-readable
- name likely readable but with ambiguity
- image quality is not fully failed, but not clearly good enough

Suggested sample classes:
- weak OCR but human-readable image
- lightly blurred date area
- low contrast print
- slightly skewed capture with readable core fields

Minimum expectation for pilot preparation:
- at least 5 boundary samples
- these should be used to calibrate REVIEW behavior, not just pass/fail tests

### Sample preparation principle

The pilot must not rely on one happy-path asset only.

At minimum, the SICK pilot should start with three buckets:
- normal bucket
- abnormal bucket
- boundary bucket

If the team cannot produce these three buckets, the SICK pilot should not be considered ready.

## B. 指标基线定义

### 1. 准确率（定义口径）

Definition:
- final SICK verification agreement rate between system conclusion and human final review conclusion

Recommended measurement rule:
- compare system output (`PASS` / `REVIEW` / `REJECT`) with the human-reviewed final result for the same case
- measure only on real or pilot-designated SICK cases, not mixed experimental noise

Suggested pilot baseline target:
- overall agreement >= 85%
- for clean normal samples, agreement target >= 90%

### 2. REVIEW率（目标区间）

Definition:
- `REVIEW` count / total processed SICK cases

Reason for tracking:
- too low means over-aggressive risk release
- too high means insufficient business efficiency value

Suggested target band for SICK pilot:
- 15% ~ 35%

Interpretation:
- below 10%: strong risk of over-trusting the model or rules
- above 45%: pilot assistance value is likely too weak

### 3. 接口成功率

Definition:
- successful `verify-attachment` responses / total SICK pilot verification calls

Suggested target:
- >= 95%

Operational note:
- success means the system returned a usable business result or explicit business-handlable error state
- silent failure or unusable response must be counted as failure

### 4. P95耗时

Definition:
- P95 end-to-end latency from approver trigger to usable verification result display

Suggested target:
- P95 < 8 seconds

Sub-targets:
- analyze P95 < 5 seconds
- verify P95 < 3 seconds

### 5. 人工复核占比

Definition:
- cases actually requiring human manual verification / total SICK pilot cases

Suggested target band:
- 20% ~ 40%

Meaning:
- pilot is useful only if many routine cases become easier, while uncertain cases are still safely routed to humans

## C. 运行 SOP

### 1. 审批人如何使用结果

Approver operating principle:
- treat the system as approval assistance,
- always read the verification result before looking at lower-level detail,
- use rule results and warnings as evidence,
- retain final human decision authority.

Recommended approver sequence:
1. view `verify_status`
2. read `summary_message`
3. inspect warnings and rule results
4. if needed, inspect request-vs-document evidence
5. decide approve / manual review / reject according to business policy

### 2. PASS / REVIEW / REJECT 如何处理

#### PASS
- continue standard approval review
- no additional attachment re-check required by default
- approver may still manually inspect if the case is sensitive

#### REVIEW
- must enter manual review
- approver checks warnings, name/date alignment, and attachment evidence
- do not treat REVIEW as approval-ready

#### REJECT
- attachment should be treated as not acceptable in its current state
- approver should reject, return, or request correction according to process policy
- final decision still belongs to the approver

### 3. OCR失败如何处理

When OCR cannot produce a reliable usable result:
- do not force PASS
- route to manual fallback
- mark the case as manual review required
- retain request_id and case trace for later analysis

Operational action:
- approver performs manual attachment inspection
- case is recorded as OCR failure in pilot statistics

### 4. 接口失败如何处理

When interface or verification request fails:
- display error clearly
- if an older result is visible, mark it as reference-only
- do not let the approver treat stale output as the latest result
- revert to manual approval review for the case

Operational action:
- approver continues manually
- pilot operations support records the failure in weekly tracking

## D. 风险说明

### 当前已知误判类型

Known or expected SICK pilot risk patterns include:

1. analysis stricter than verification
- analysis may suggest stronger caution than final verification result
- this is not necessarily a bug, but it must be explainable

2. weak image but partial field extraction
- the system may read some core fields while quality remains poor
- these cases should bias toward REVIEW instead of easy PASS

3. date ambiguity
- leave dates may appear aligned in structure but still be weak in OCR certainty
- these are boundary review candidates

4. incomplete medical context
- core date fields may exist while hospital / diagnosis / physician context is weak or missing
- these cases may still need human review depending on policy strictness

### 哪些情况必须人工复核

The following SICK cases must go to human manual review:

- `verify_status=REVIEW`
- any technical error in verification flow
- OCR failure or unreadable core field area
- applicant name cannot be trusted
- leave date comparison cannot be trusted
- stale result is displayed after a failed new request
- approver believes the case is sensitive or uncertain despite system output

## E. 验收标准

The SICK pilot should be considered ready to enter controlled business pilot only if all of the following are true:

1. `docs/contract-pilot-v1.md` is already Confirmed
2. the SICK sample system is prepared in three buckets:
   - normal
   - abnormal
   - boundary
3. the metric baseline definition is accepted by product, QA, and business owner
4. approver-side SOP is documented and understandable
5. manual fallback rule is operationally accepted
6. no known blocker prevents SICK-only pilot launch

### Minimum launch gate

Do not declare SICK pilot readiness if any of the following is missing:
- normal/abnormal/boundary sample grouping
- clear REVIEW target band
- clear manual fallback behavior
- clear P95 latency target
- clear agreement-rate measurement method

## Risks

| Risk | Description | Control |
|---|---|---|
| Happy-path bias | only clean samples are prepared | require 3-bucket sample system |
| Over-release risk | REVIEW ratio too low, weak cases escape manual review | keep conservative REVIEW band |
| Low business value | REVIEW ratio too high, almost everything goes manual | measure and tune after pilot starts |
| Operational confusion | approvers do not know how to handle REVIEW or stale/error states | use the SOP section as mandatory training basis |

## Next Action Items

1. Build the actual SICK sample register using the three-bucket structure in this document.
2. Create metrics tracking documents using these baseline definitions.
3. Validate that pilot approvers understand the SICK SOP before live pilot use.
4. Keep marriage work out of this stage until SICK readiness is stable.
