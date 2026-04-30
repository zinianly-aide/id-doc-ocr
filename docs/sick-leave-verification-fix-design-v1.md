# Sick Leave Verification Fix Design v1

## Background

This document is the follow-up design artifact to:

- `docs/sick-leave-verification-gap-analysis-v1.md`
- `docs/pilot-sick-leave-samples-v1.md`

The current verified issue is limited and clear:

- in `leave_type=SICK`
- some weak real-image samples already produce `analysis.review_action = reject` or `review`
- but the final `verification.verify_status` is still `PASS`

This document defines the minimum controllable repair design before any code implementation begins.

## Scope Constraints

This design is intentionally narrow.

Allowed:
- SICK verification decision tightening
- using existing analysis / verification fields only
- minimal gating before final PASS

Not allowed:
- contract changes
- new document types
- marriage-scope expansion
- large verification-engine rewrite
- v2 architecture redesign

---

## A. 修复目标（必须量化）

### Goal 1 — Eliminate Type A

Definition of Type A:
- `analysis.review_action = reject`
- final `verify_status = PASS`

Target:
- for the known conflict regression set, Type A count must go from `4` to `0`

Current confirmed Type A samples:
- `online_prescription_laptop.jpg`
- `online_prescription_mobile.jpg`
- `certificado_medico.jpg`
- `handwritten_prescription_1940.jpg`

### Goal 2 — Control Type B

Definition of Type B:
- `analysis.review_action = review`
- and the sample is explicitly weak for SICK business use
- but final `verify_status = PASS`

Target:
- for the known conflict regression set, Type B count must go from `1` to `0`
- specifically for `medical_record` weak-signal SICK cases, final PASS must be blocked

Current confirmed Type B sample:
- `illness_history_thumb.jpg`

### Goal 3 — Do not significantly increase false blocking

Design guardrail:
- `PASS -> REVIEW` transitions should be limited to clearly weak candidate-PASS samples
- `PASS -> REJECT` transitions should be `0` in the first repair wave unless already required by existing downstream rules

Quantified first-wave target on the current 19-sample registry:
- expected `PASS -> REVIEW`: `9`
- expected `PASS -> REJECT`: `0`
- expected impact on current Normal samples: `0 / 3`

---

## B. 修复策略（只允许最小改动）

### Strategy summary

The first repair wave should add a narrow PASS gating layer for `leave_type=SICK` only.

It should not redesign the existing verification pipeline. It should only stop unsafe PASS results from being emitted.

### 1. 是否引入 gating

Yes.

Introduce a minimal pre-PASS gating step:
- only for `leave_type=SICK`
- only when the current verification candidate result is `PASS`
- only using already available analysis / verification fields

### 2. gating 条件具体表达式（伪代码级别）

#### Gating rule A — reject-level analysis cannot end in PASS

```python
if leave_type == "SICK" and candidate_verify_status == "PASS":
    if analysis.risk.review_action == "reject":
        final_verify_status = "REVIEW"
```

Design intent:
- eliminate Type A with minimum blast radius
- do not introduce new contract fields
- do not redesign scoring

#### Gating rule B — weak `medical_record` sick-note signal cannot end in PASS

```python
if leave_type == "SICK" and candidate_verify_status == "PASS":
    if analysis.doc_type == "medical_record":
        issue_codes = {issue.code for issue in analysis.validation.issues}
        if "not_sick_note_like" in issue_codes or "weak_sick_note_signal" in issue_codes:
            final_verify_status = "REVIEW"
```

Design intent:
- control Type B without expanding scope into broader review heuristics
- target only the currently confirmed weak-signal medical-record path

#### Gating rule C — minimum PASS evidence for SICK

This should be evaluated only after rule A and rule B pass.

```python
if leave_type == "SICK" and candidate_verify_status == "PASS":
    fields = verification.extracted_fields

    has_patient = bool(fields.get("patient_name"))
    has_leave_evidence = bool(
        fields.get("rest_start_date") or
        fields.get("rest_end_date") or
        fields.get("rest_days") or
        fields.get("issue_date")
    )

    if not (has_patient and has_leave_evidence):
        final_verify_status = "REVIEW"
```

Design intent:
- keep PASS from being granted when extracted field evidence is nearly empty
- use only existing fields
- avoid stricter requirements like mandatory diagnosis / seal in the first repair wave

### 3. SICK PASS 最小字段要求（不新增字段，只使用已有字段）

For the first repair wave, SICK `PASS` should require at least:

1. `patient_name` present
2. at least one leave-related evidence field present:
   - `rest_start_date`, or
   - `rest_end_date`, or
   - `rest_days`, or
   - `issue_date`
3. `analysis.risk.review_action != reject`
4. if `analysis.doc_type == medical_record`, then validation must not include:
   - `not_sick_note_like`
   - `weak_sick_note_signal`

This is intentionally minimal.

It does not require:
- new fields
- new attachment labels
- new diagnosis parsing logic
- new doc_type taxonomy

---

## C. 规则优先级与执行顺序

### 当前 verify 判定顺序（概念层）

Based on current observed behavior, the effective order appears close to:

1. classify attachment / expected attachment type
2. run request-vs-document rule checks
3. aggregate verification result
4. emit final `PASS / REVIEW / REJECT`

Current observed issue:
- attachment-type match appears strong enough to preserve PASS,
- even when analysis has already concluded the image is too weak.

### 修复后顺序（必须前置 gating）

Proposed first-wave order:

1. run analysis as today
2. build candidate verification result as today
3. if candidate result is not `PASS`, keep current behavior unchanged
4. if candidate result is `PASS` and `leave_type == SICK`, apply pre-PASS gating:
   - Gating A: `analysis.review_action == reject` -> downgrade to `REVIEW`
   - Gating B: weak `medical_record` sick-note signal -> downgrade to `REVIEW`
   - Gating C: minimum SICK PASS field evidence check -> downgrade to `REVIEW`
5. emit final `PASS / REVIEW / REJECT`

### Why gating must be pre-PASS, not post-hoc explanation only

If the system keeps emitting PASS and only adds explanation text later, the business-risk problem remains.

The repair must change decision output, not only wording.

---

## D. 影响评估

### Impact estimate on the current 19-sample registry

Estimated first-wave impact:

- `PASS -> REVIEW`: `9`
- `PASS -> REJECT`: `0`
- `REVIEW -> PASS`: `0`
- `REVIEW -> REJECT`: `0`

### Why `PASS -> REVIEW = 9`

These are the currently known weak public PASS cases expected to be downgraded:

1. `online_prescription_laptop.jpg`
2. `online_prescription_mobile.jpg`
3. `illness_history_thumb.jpg`
4. `certificado_medico.jpg`
5. `handwritten_prescription_1940.jpg`
6. `handwritten_prescription_1935_thumb.jpg`
7. `medical_care_card_usa_sample.jpg`
8. `kassenrezept_at.jpg`
9. `privatrezept_blancorezept_thumb.jpg`

### Why `PASS -> REJECT = 0`

The first repair wave should stay conservative.

Reason:
- the confirmed problem is over-permissive PASS,
- not missing hard-reject routing,
- and REVIEW is the safest first-wave downgrade that preserves human fallback.

### 是否影响正常样本（Normal）

Estimated effect on current Normal samples: no meaningful impact.

Expected Normal sample outcomes:

- `diagnosis_certificate_text.expected.json`
  - should remain PASS
- `verify-attachment.success.pass.json`
  - should remain PASS
- `approval-verification-page.pass.json`
  - should remain PASS

Reasoning:
- the design does not blanket-convert all `analysis.review_action = review` cases,
- the design only blocks PASS for:
  - reject-level analysis, or
  - weak `medical_record` sick-note signal, or
  - missing minimal patient/leave evidence

That keeps the current clean PASS demo/control path stable.

---

## E. 回归验证方案

### Primary regression source

Use:
- `docs/pilot-sick-leave-samples-v1.md`

This remains the source-of-truth registry for first-wave regression.

### 关键回归样本（critical）

#### Must-pass repair-target set

- `online_prescription_laptop.jpg`
- `online_prescription_mobile.jpg`
- `illness_history_thumb.jpg`
- `certificado_medico.jpg`
- `handwritten_prescription_1940.jpg`

Expected result after fix:
- none of these may end with `verify_status = PASS`
- each should move to `REVIEW`

#### Extended weak-image regression set

- `handwritten_prescription_1935_thumb.jpg`
- `medical_care_card_usa_sample.jpg`
- `kassenrezept_at.jpg`
- `privatrezept_blancorezept_thumb.jpg`

Expected result after fix:
- each should move from weak PASS to REVIEW

#### Normal control set

- `diagnosis_certificate_text.expected.json`
- `verify-attachment.success.pass.json`
- `approval-verification-page.pass.json`

Expected result after fix:
- remain PASS

#### Existing review-control set

- `diagnosis_certificate_minimal.expected.json`
- `basic_outpatient_note.expected.json`
- `sick_note_like.expected.json`
- `analyze-document.boundary.partial-analysis.json`

Expected result after fix:
- remain REVIEW-oriented, no accidental PASS promotion

### 验收通过标准

The first repair wave passes acceptance only if all of the following are true:

1. all five known conflict samples stop returning PASS
2. all known weak public medical-document samples in the extended set stop returning PASS
3. current Normal control samples remain PASS
4. no contract field changes are introduced
5. no marriage-scope behavior is changed
6. no new doc_type is introduced

---

## F. 风险与边界

### 是否可能导致 REVIEW率过高

Yes, but this is expected and acceptable in the first wave.

Reason:
- the current problem is unsafe PASS,
- the first repair wave intentionally prefers human fallback over optimistic approval.

Mitigation principle:
- first wave should downgrade weak PASS to REVIEW,
- not attempt a broader scoring redesign.

### 是否影响 UI 解释成本

Yes, slightly.

Why:
- more cases will show REVIEW instead of PASS,
- and product/UI may need to explain that PASS is now more conservative.

However, this is manageable because:
- contract is unchanged,
- UI already supports REVIEW state,
- explanation complexity is lower than allowing unsafe PASS.

### 是否需要业务再确认（仅标注，不发起）

Yes.

Suggested business-confirmation topic:
- whether the first repair wave should downgrade all weak PASS cases to REVIEW,
- and whether any narrow business exception exists.

This document only flags that the confirmation may be needed. It does not initiate it.

### 边界说明

This design intentionally does not decide:
- whether some cases should become REJECT instead of REVIEW,
- whether diagnosis must become a mandatory PASS field,
- whether seal/physician evidence should become hard PASS gates,
- whether review scoring itself should be refactored.

Those are out of scope for the first minimal repair wave.
