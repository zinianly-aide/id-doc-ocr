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
| SICK-N-001 | sick_normal_placeholder_001.jpg | Normal | 标准清晰病假证明，姓名与日期完整可读 | diagnosis_proof | PASS | Yes | 模拟 | No | 首批 happy-path 基线样本占位 |
| SICK-N-002 | sick_normal_placeholder_002.jpg | Normal | 标准清晰病假证明，版式与 N-001 不同 | diagnosis_proof | PASS | Yes | 模拟 | No | 用于版式差异覆盖 |
| SICK-A-001 | sick_abnormal_placeholder_001.jpg | Abnormal | 姓名字段缺失或不可读 | diagnosis_proof | REVIEW | Yes | 模拟 | No | 关键异常样本，占位待真实替换 |
| SICK-A-002 | sick_abnormal_placeholder_002.jpg | Abnormal | 日期字段部分模糊，影响休假起止判断 | diagnosis_proof | REVIEW | Yes | 模拟 | No | 用于字段缺失/模糊验证 |
| SICK-E-001 | sick_edge_placeholder_001.jpg | Edge | 轻微模糊但人工仍可识别核心字段 | diagnosis_proof | REVIEW | Yes | 模拟 | No | 用于边界 REVIEW 校准 |

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
