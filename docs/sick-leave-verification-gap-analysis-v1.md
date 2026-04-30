# Sick Leave Verification Gap Analysis v1

## 背景

The project has already reached the stage where SICK leave samples can be run through both:

- `POST /analyze-document`
- `POST /verify-attachment`

During P2.2 sample population, a new batch of public medical-document-adjacent images was added and executed against the real local service.

That run surfaced a consistent and important pattern:

- `analysis.validation.accepted = false`
- `analysis.risk.review_action = reject` or `review`
- but `verification.verify_status = PASS`

This document does not change rules, does not change the contract, does not expand to `MARRIAGE`, and does not introduce new document types.

Its purpose is to turn the current problem into a reviewable and repairable governance artifact before any rule changes begin.

## 问题定义

### Core problem

For multiple SICK-related public real-image samples, the current verification chain shows:

1. the analysis layer already indicates that the document is weak, incomplete, or operationally unsafe,
2. but the business verification layer still returns `PASS`,
3. and the final result therefore looks approval-safe even when the extracted evidence is clearly insufficient.

### Why this is a real gap

In the current pilot scope, `PASS` is the strongest business signal. If weak medical-document samples receive `PASS` while the analysis layer is already rejecting or flagging them, the system creates a false sense of reliability for approvers.

### Scope of this gap document

In scope:
- `leave_type=SICK`
- current contract behavior only
- currently observed `analysis reject/review` vs `verify PASS` conflicts
- real public sample evidence from P2.2

Out of scope:
- rule code changes
- contract adjustment
- `MARRIAGE`
- new document-type introduction

## 受影响样本清单

The following samples are confirmed conflict cases and must be included in the first remediation wave:

1. `online_prescription_laptop.jpg`
2. `online_prescription_mobile.jpg`
3. `illness_history_thumb.jpg`
4. `certificado_medico.jpg`
5. `handwritten_prescription_1940.jpg`

All five were executed against the real local service during P2.2.

## analysis 结论

### Common observed analysis pattern

Across the affected samples, the analysis layer commonly shows one or more of these conditions:

- `validation.accepted = false`
- `risk.review_action = reject` or `review`
- core fields missing
- weak or unsuitable document structure
- insufficient evidence to support a safe sick-leave verification decision

### Sample-by-sample analysis summary

| 样本 | plugin route | analysis doc_type | validation.accepted | analysis review_action | 主要 analysis 问题 |
|---|---|---|---|---|---|
| `online_prescription_laptop.jpg` | `diagnosis_proof` | `diagnosis_proof` | false | reject | missing_hospital_name, missing_diagnosis, missing_issue_date, missing_certificate_title, missing_advice, missing_physician_name, missing_department, missing_seal |
| `online_prescription_mobile.jpg` | `diagnosis_proof` | `diagnosis_proof` | false | reject | same missing-core-field pattern as laptop prescription |
| `illness_history_thumb.jpg` | `medical_record` | `medical_record` | false | review | missing_patient_name, missing_visit_date, `not_sick_note_like`, `weak_sick_note_signal` |
| `certificado_medico.jpg` | `diagnosis_proof` | `diagnosis_proof` | false | reject | same missing-core-field pattern; visually closest to a certificate but still not sufficiently parsed |
| `handwritten_prescription_1940.jpg` | `diagnosis_proof` | `diagnosis_proof` | false | reject | same missing-core-field pattern under handwritten OCR stress |

## verification 结论

Despite the analysis-layer weakness above, all five samples currently produce the same business-facing verification pattern:

- `verify_status = PASS`
- `risk_level = LOW`
- `matched_attachment_type = MEDICAL_CERTIFICATE`
- `warnings = []`
- `needs_manual_review = false`

### Sample-by-sample verification summary

| 样本 | verify_status | risk_level | matched_attachment_type | needs_manual_review | verification summary |
|---|---|---|---|---|---|
| `online_prescription_laptop.jpg` | PASS | LOW | MEDICAL_CERTIFICATE | false | `PASS: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']` |
| `online_prescription_mobile.jpg` | PASS | LOW | MEDICAL_CERTIFICATE | false | `PASS: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']` |
| `illness_history_thumb.jpg` | PASS | LOW | MEDICAL_CERTIFICATE | false | `PASS: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']` |
| `certificado_medico.jpg` | PASS | LOW | MEDICAL_CERTIFICATE | false | `PASS: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']` |
| `handwritten_prescription_1940.jpg` | PASS | LOW | MEDICAL_CERTIFICATE | false | `PASS: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']` |

## 冲突类型

### Type A — Validation reject but business PASS

Pattern:
- `validation.accepted = false`
- `analysis.review_action = reject`
- final `verify_status = PASS`

Affected samples:
- `online_prescription_laptop.jpg`
- `online_prescription_mobile.jpg`
- `certificado_medico.jpg`
- `handwritten_prescription_1940.jpg`

### Type B — Not-sick-note-like / weak-signal but business PASS

Pattern:
- `medical_record` route identifies weak or non-sick-note behavior
- `analysis.review_action = review`
- final `verify_status = PASS`

Affected sample:
- `illness_history_thumb.jpg`

### Type C — Attachment-label pass dominating field-level weakness

Pattern:
- attachment-type matching appears to be sufficient for PASS,
- even when extracted core medical-proof fields are empty or unsuitable.

Affected samples:
- all five required samples

## 可能根因

This section lists hypotheses only. It is not yet a code-level diagnosis.

### 1. Verification is overweighting attachment-type match

The verification layer may be treating `MEDICAL_CERTIFICATE` classification match as the dominant signal, while underweighting missing fields and analysis-layer rejection evidence.

### 2. Analysis rejection is not being promoted into verification gating

Current verification behavior suggests that `analysis.validation.accepted = false` and `analysis.risk.review_action = reject/review` are not hard blockers for business `PASS`.

### 3. Core-field sufficiency is not enforced before PASS

The verification layer may lack a minimum-field sufficiency gate for SICK leave, such as requiring enough evidence for:
- hospital/source identity
- diagnosis or sick-note semantics
- issue/rest dates
- physician/seal evidence when applicable

### 4. medical_record weak-signal results are not mapped safely into SICK business decisions

For `medical_record` samples with `not_sick_note_like` or `weak_sick_note_signal`, the verification layer still returns `PASS`, which suggests weak handoff between parser-specific quality signals and business decision logic.

### 5. Public weak-image / non-standard-image behavior is underrepresented in PASS gating design

The current PASS path may be calibrated around internal fixture assumptions rather than weak real-image evidence.

## 风险等级

Overall risk level for this gap: HIGH

### Why HIGH

- `PASS` is the strongest approval-facing positive conclusion.
- The gap affects real public images, not only synthetic mocks.
- The conflict is repeated across multiple sample styles.
- The current output may cause approvers to over-trust weak evidence.

### Risk by operational dimension

| 风险维度 | 等级 | 说明 |
|---|---|---|
| 业务误放行风险 | High | weak or unsuitable medical documents may receive PASS |
| 审批信号可信度风险 | High | analysis and verification tell different stories |
| 试点治理风险 | High | pilot metrics may look better than actual evidence quality supports |
| contract 风险 | Low | no contract mismatch observed; the issue is semantic decision behavior |
| 文档类型扩散风险 | Medium | non-standard medical artifacts can be accepted as PASS under SICK expectations |

## 建议修复方向

This section defines minimal repair direction, not implementation.

### Direction 1 — Introduce PASS preconditions for SICK verification

Define a minimal business rule that `PASS` is not allowed when analysis already indicates operationally insufficient evidence.

Candidate principle:
- if `analysis.validation.accepted = false`, `PASS` should generally be blocked unless a narrowly defined override exists.

### Direction 2 — Promote analysis risk/review signals into verification decision gating

Candidate principle:
- `analysis.review_action = reject` must not end in `verify_status = PASS`
- `analysis.review_action = review` should default toward `REVIEW`, not `PASS`, unless additional strong evidence exists

### Direction 3 — Add minimum field sufficiency expectations for SICK

Candidate principle:
A SICK `PASS` should require enough business evidence, not only attachment-label match.

This does not require new document types. It only requires a clearer minimum evidence threshold for the existing SICK path.

### Direction 4 — Treat weak `medical_record` sick-note signals conservatively

Candidate principle:
If `medical_record` analysis returns `not_sick_note_like` or `weak_sick_note_signal`, final verification should not be `PASS`.

### Direction 5 — Keep remediation minimal and scoped

Constraints for repair phase:
- do not change contract v1
- do not add new document types
- do not expand to `MARRIAGE`
- only tighten SICK PASS gating and conflict handling

## 修复验收标准

A future repair should be considered accepted only if the following are all true:

### A. Conflict elimination on known cases

For the five required conflict samples:
- `online_prescription_laptop.jpg`
- `online_prescription_mobile.jpg`
- `illness_history_thumb.jpg`
- `certificado_medico.jpg`
- `handwritten_prescription_1940.jpg`

Expected acceptance condition:
- no sample ends with `verify_status = PASS` while analysis still indicates reject/review-level insufficiency.

### B. PASS semantics become conservative and explainable

Expected acceptance condition:
- `PASS` only appears when evidence quality is sufficient,
- and weak-field / weak-signal samples move to `REVIEW` or `REJECT` as appropriate.

### C. Existing known good baseline is preserved

Expected acceptance condition:
- the current clean positive baseline samples do not regress unexpectedly,
- especially the existing internal PASS baseline already used in docs / demo.

### D. Regression outputs are reviewable

Expected acceptance condition:
- sample-by-sample before/after status can be tabulated,
- and each changed sample has an explicit rationale.

## 回归样本范围

### Priority 1 — Must-run conflict regression set

- `online_prescription_laptop.jpg`
- `online_prescription_mobile.jpg`
- `illness_history_thumb.jpg`
- `certificado_medico.jpg`
- `handwritten_prescription_1940.jpg`

### Priority 2 — Same-family weak-image extension set

- `handwritten_prescription_1935_thumb.jpg`
- `medical_care_card_usa_sample.jpg`
- `kassenrezept_at.jpg`
- `privatrezept_blancorezept_thumb.jpg`

### Priority 3 — Internal baseline control set

- `diagnosis_certificate_text.expected.json`
- `diagnosis_certificate_minimal.expected.json`
- `basic_outpatient_note.expected.json`
- `sick_note_like.expected.json`
- `verify-attachment.success.pass.json`
- `approval-verification-page.pass.json`

## 建议评审结论模板

Recommended review conclusion format for the next stage:

1. confirm this is a real SICK verification gap,
2. confirm no contract change is needed,
3. confirm first repair wave should only tighten PASS gating,
4. confirm no marriage-scope expansion is included,
5. approve entry into a minimal rule-remediation phase after this document is reviewed.
