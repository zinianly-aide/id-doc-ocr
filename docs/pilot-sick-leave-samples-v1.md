# Sick Leave Sample Registry v1

## Background

This document converts the SICK leave sample-system definition into an operable sample registry baseline.

It is intended to support the first pilot track only:

- leave type: `SICK`
- attachment expectation: `MEDICAL_CERTIFICATE`
- single attachment
- single image
- approval assistance only

This document does not add new rules, does not change the contract, and does not expand to `MARRIAGE`.

## Goal

Build a structured sample registry that can be used repeatedly for:

1. integration testing,
2. regression verification,
3. misjudgment analysis,
4. pilot readiness tracking.

## Scope

### In Scope
- SICK leave sample registration
- sample classification and tracking
- expected verification outcome management
- validation status tracking

### Out of Scope
- new verification rule design
- contract adjustment
- MARRIAGE scenario expansion
- PDF and multi-attachment expansion

## A. 样本分类结构

The sample registry must always be managed using three buckets.

### 1. Normal（正常样本）

Definition:
- clear, standard, usable samples
- core fields are readable
- suitable for validating the routine successful path

Typical purpose:
- verify stable standard processing
- verify expected PASS behavior or low-friction REVIEW behavior
- establish the happy-path baseline

### 2. Abnormal（异常样本）

Definition:
- samples with missing fields, blur, occlusion, crop loss, or clearly risky quality problems
- suitable for validating safe handling of weak or incomplete material

Typical purpose:
- verify REVIEW / REJECT routing
- prevent over-release of risky material
- record recurring failure modes

### 3. Edge（边界样本）

Definition:
- borderline samples between clearly usable and clearly unusable
- OCR may be weak, dates may be ambiguous, image quality may be human-readable but machine-unstable

Typical purpose:
- validate borderline REVIEW behavior
- calibrate where manual review should intervene
- support later misjudgment analysis

## B. 样本台账表

The registry below is the minimum structured ledger template. New samples should be appended instead of replacing historical entries.

| sample_id | 文件名 | 类型（Normal / Abnormal / Edge） | 场景说明 | 期望 doc_type | 期望 verify_status（PASS / REVIEW / REJECT） | 是否关键样本（Yes/No） | 来源（真实 / 模拟） | 是否已验证（Yes/No） | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| SICK-N-001 | diagnosis_certificate_text.expected.json | Normal | 脱敏诊断证明文本 fixture，字段完整，医院/诊断/休假日期齐全 | diagnosis_proof | PASS | Yes | 真实 | Yes | 当前仓库里最接近标准病假证明的稳定基线样本 |
| SICK-N-002 | verify-attachment.success.pass.json | Normal | mock 完整核验 PASS 场景，申请人与请假日期全部对齐 | diagnosis_proof | PASS | Yes | 模拟 | Yes | 业务结论稳定为 PASS，可作为联调 happy-path |
| SICK-N-003 | approval-verification-page.pass.json | Normal | 前端页面级 PASS 场景，覆盖 analyze + verify 联合展示 | diagnosis_proof | PASS | No | 模拟 | Yes | 用于 UI 回归，确保审批页能稳定展示 PASS |
| SICK-N-004 | diagnosis_generated_001.png | Normal | 生成版标准门诊诊断证明，字段完整，接近标准病假证明版式 | diagnosis_proof | PASS | Yes | 模拟 | Yes | 实测：analysis.review_action=review，verify=PASS，risk=LOW，未误降 |
| SICK-N-005 | diagnosis_generated_002.png | Normal | 生成版标准疾病诊断证明，结构完整，轻微缺失印章识别 | diagnosis_proof | PASS | No | 模拟 | Yes | 实测：analysis.review_action=review，issues=missing_seal，verify=PASS，未误降 |
| SICK-N-006 | diagnosis_generated_003.png | Normal | 生成版门诊疾病诊断证明，医院/诊断/休假日期完整 | diagnosis_proof | PASS | Yes | 模拟 | Yes | 实测：analysis.review_action=review，verify=PASS，risk=LOW，未误降 |
| SICK-N-007 | diagnosis_generated_004.png | Normal | 生成版疾病诊断证明，消化内科标准病假证明场景 | diagnosis_proof | PASS | No | 模拟 | Yes | 实测：analysis.review_action=review，verify=PASS，risk=LOW，未误降 |
| SICK-N-008 | diagnosis_generated_005.png | Normal | 生成版门诊诊断证明，耳鼻喉科标准休假建议场景 | diagnosis_proof | PASS | No | 模拟 | Yes | 实测：analysis.review_action=review，verify=PASS，risk=LOW，未误降 |
| SICK-N-009 | diagnosis_generated_006.png | Normal | 生成版疾病诊断证明，呼吸科标准病假证明场景 | diagnosis_proof | PASS | No | 模拟 | Yes | 实测：analysis.review_action=review，issues=missing_seal，verify=PASS，未误降 |
| SICK-N-010 | diagnosis_generated_007.png | Normal | 生成版门诊诊断证明，全科医学科标准请假场景 | diagnosis_proof | PASS | Yes | 模拟 | Yes | 实测：analysis.review_action=review，verify=PASS，risk=LOW，未误降 |
| SICK-N-011 | diagnosis_generated_008.png | Normal | 生成版疾病诊断证明，神经内科标准病假证明场景 | diagnosis_proof | PASS | No | 模拟 | Yes | 实测：analysis.review_action=review，verify=PASS，risk=LOW，未误降 |
| SICK-A-001 | diagnosis_certificate_minimal.expected.json | Abnormal | 脱敏最小诊断证明文本，休假起止日期与盖章缺失 | diagnosis_proof | REVIEW | Yes | 真实 | Yes | 关键缺口：字段不完整，适合验证人工复核入口 |
| SICK-A-002 | basic_outpatient_note.expected.json | Abnormal | 门诊病历文本，不是标准诊断证明/病休证明 | medical_record | REVIEW | Yes | 真实 | Yes | 风险点：更像 medical_record，不能直接按标准病假证明放行 |
| SICK-A-003 | analyze-document.success.json | Abnormal | mock analyze 返回 diagnosis_proof，但 validation 明确缺失医院和诊断 | diagnosis_proof | REVIEW | No | 模拟 | Yes | 识别问题：missing_hospital_name / missing_diagnosis |
| SICK-A-004 | verify-attachment.error.missing-expected.json | Abnormal | verify 请求缺少 expected attachment type 的错误场景 | diagnosis_proof | REVIEW | No | 模拟 | No | 当前是接口错误样本；运营口径应转人工复核，不可自动放行 |
| SICK-E-001 | sick_note_like.expected.json | Edge | 病休证明风格明显，但插件仍归类为 medical_record 的边界文本 | medical_record | REVIEW | Yes | 真实 | Yes | 关键边界样本：sick_note_like 命中高，但 attachment 语义仍需人工判断 |
| SICK-E-002 | analyze-document.boundary.partial-analysis.json | Edge | mock partial-analysis 场景，姓名/日期在，但医院与医师信息不完整 | diagnosis_proof | REVIEW | Yes | 模拟 | Yes | 风险点：partial fields + weak perspective confidence |
| SICK-E-003 | analyze-document.error.missing-plugin.json | Edge | analyze 请求缺少 plugin_name 的配置错误场景 | diagnosis_proof | REVIEW | No | 模拟 | No | 当前是接入配置边界，不属于文档识别错误；应阻断自动化并人工处理 |
| SICK-A-005 | online_prescription_laptop.jpg | Abnormal | 公开在线处方截图，diagnosis_proof 路由下无法抽出医院/诊断/日期等核心字段 | diagnosis_proof | PASS | Yes | 真实 | Yes | 关键冲突样本：analysis=reject，但 verify 仍返回 PASS |
| SICK-A-006 | online_prescription_mobile.jpg | Abnormal | 公开手机在线处方截图，字段抽取几乎为空 | diagnosis_proof | PASS | Yes | 真实 | Yes | 关键冲突样本：missing_hospital_name/missing_diagnosis/missing_seal，但 verify=PASS |
| SICK-A-007 | handwritten_prescription_1940.jpg | Abnormal | 公开手写处方，真实 OCR 压力高，当前 diagnosis_proof 校验几乎全缺失 | diagnosis_proof | PASS | No | 真实 | Yes | 高风险手写异常样本；analysis=reject 与 verify=PASS 冲突明显 |
| SICK-A-008 | handwritten_prescription_1935_thumb.jpg | Abnormal | 公开手写处方缩略图，识别质量进一步下降 | diagnosis_proof | PASS | No | 真实 | Yes | 缩略图+手写双重弱质，仍被 verify 判为 PASS |
| SICK-A-009 | illness_history_thumb.jpg | Abnormal | 公开病史页，medical_record 路由下 not_sick_note_like，不能视为有效病假证明 | medical_record | PASS | Yes | 真实 | Yes | 关键冲突样本：sick_note_check=low 且 not_sick_note_like，但 verify=PASS |
| SICK-A-010 | medical_care_card_usa_sample.jpg | Abnormal | 公开医疗卡样本，不是病假证明，但被 diagnosis_proof 路由收下 | diagnosis_proof | PASS | No | 真实 | Yes | 非证明类医疗卡，适合作为误判分析样本 |
| SICK-E-004 | certificado_medico.jpg | Edge | 公开 medical certificate 图片，最接近病假证明外观，但当前字段解析仍不完整 | diagnosis_proof | PASS | Yes | 真实 | Yes | 最接近公开正样本；目前仍出现 analysis=reject / verify=PASS |
| SICK-E-005 | kassenrezept_at.jpg | Edge | 公开处方单据，具医疗文书外观但与病假证明字段不一致 | diagnosis_proof | PASS | No | 真实 | Yes | 适合验证“附件像医疗单据但不是标准病假证明”的边界情况 |
| SICK-E-006 | privatrezept_blancorezept_thumb.jpg | Edge | 公开私人处方缩略图，结构像医疗文书但字段不足 | diagnosis_proof | PASS | No | 真实 | Yes | 缩略图处方边界样本；当前 verify 仍偏宽松 |

### 字段说明

- `sample_id`
  - unique sample identifier
  - recommended pattern: `SICK-N-001`, `SICK-A-001`, `SICK-E-001`
- `文件名`
  - actual file name or stable storage reference
- `类型`
  - must be one of `Normal`, `Abnormal`, `Edge`
- `场景说明`
  - short human-readable scenario summary
- `期望 doc_type`
  - expected extracted document type for regression comparison
- `期望 verify_status`
  - expected business result: `PASS`, `REVIEW`, or `REJECT`
- `是否关键样本`
  - whether this sample is part of the minimum must-pass regression set
- `来源`
  - `真实` or `模拟`
- `是否已验证`
  - whether the sample has already been run and confirmed against the current baseline
- `备注`
  - free-form note for risk mode, ownership, replacement plan, or traceability

## C. 最小样本规模要求

The SICK pilot registry is not considered operationally ready unless the following minimum size exists:

- Normal ≥ 10
- Abnormal ≥ 10
- Edge ≥ 5

Recommended interpretation:
- Normal samples establish routine-path confidence
- Abnormal samples establish safe fallback confidence
- Edge samples establish manual-review boundary confidence

Practical rule:
- before the pilot starts, all three buckets must exist,
- and at least the key samples should be marked as verified.

### 当前填充状态（repo baseline）

Current evidence-backed population progress in this repository:

- Normal: 11 / 10
- Abnormal: 10 / 10
- Edge: 6 / 5
- Critical cases: 13 / 5+
- Real-source ratio: 13 / 27 = 48.1%

Interpretation:
- the registry now meets the minimum target across all three buckets,
- the new Normal sample wave confirms that current SICK PASS gating is not excessively conservative on standard diagnosis-proof-like images,
- newly generated Normal images consistently kept `verify_status = PASS`,
- public weak-image samples remain valuable as PASS-gating regression cases.

## D. 使用方式说明

### 1. 用于联调

Use the sample registry as the fixed input list for API and UI integration runs.

Recommended usage:
- pick representative samples from all three buckets,
- run `/analyze-document` and `/verify-attachment`,
- compare actual output against expected `doc_type` and expected `verify_status`,
- record mismatches in the remark column or related issue log.

### 2. 用于回归

Use the registry as the stable regression baseline whenever the UI, adapter, OCR path, or verification logic is adjusted.

Recommended usage:
- maintain a minimum key-sample subset,
- rerun all key samples before milestone closure,
- treat unexpected output drift as regression unless explicitly approved.

### 3. 用于误判分析

Use the registry to track false PASS, false REVIEW, false REJECT, and weak OCR edge behavior.

Recommended usage:
- add notes when a sample outcome differs from human expectation,
- group recurring problems by field-missing, name mismatch, date ambiguity, blur, crop, or layout issue,
- use the registry as the source list for later metrics and risk review.

## Suggested Operating Notes

- Real samples should gradually replace placeholder simulated samples.
- Critical samples should be protected from accidental deletion or silent replacement.
- The registry should be versioned through normal document governance, not maintained as an untracked spreadsheet outside the repo.
- If the team cannot fill the minimum sample size, the SICK pilot should remain in readiness mode rather than launch mode.
