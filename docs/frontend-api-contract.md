# Frontend API contract for attachment analysis and verification

## Goal

This document freezes the current frontend-facing contract for:

- `POST /analyze-document`
- `POST /verify-attachment`

The goal of this phase is frontend integration readiness, not deeper OCR capability.

## 1. `POST /analyze-document`

Recognition-only endpoint.

Use it when the page needs:
- upload preview
- OCR / extraction column
- document classification and field inspection
- debugging without business verification context

### Request fields

| Field | Type | Required | Example | Frontend usage | Notes |
| --- | --- | --- | --- | --- | --- |
| `plugin_name` | string | yes* | `diagnosis_proof` | route to the correct parser | `plugin` alias is also accepted |
| `plugin` | string | no | `diagnosis_proof` | legacy alias only | prefer `plugin_name` in new frontend code |
| `file` | binary | yes | uploaded image/pdf bytes | source attachment | multipart file upload |
| `ocr_backend` | string | no | `mock` | debugging / backend override | optional; service default is used when omitted |
| `vlm_backend` | string | no | `mock` | debugging / backend override | optional |
| `detector_backend` | string | no | `mock` | debugging / backend override | optional |
| `rectify_backend` | string | no | `mock` | debugging / backend override | optional |
| `failure_dir` | string | no | `data/failures` | backend persistence only | usually omit in frontend |
| arbitrary field overrides | string | no | `patient_name`, `rest_start_date` | parser assistance / demo injection | any non-reserved form field is forwarded into runner `fields` |

*One of `plugin_name` or `plugin` must be provided.

### Response fields

Top-level response:

| Field | Type | Always present | Frontend usage | Notes |
| --- | --- | --- | --- | --- |
| `filename` | string | yes | attachment card title | uploaded filename |
| `content_type` | string | yes | preview renderer selection | image/jpeg, image/png, application/pdf, etc. |
| `result` | object | yes | debug drawer / developer mode | full low-level pipeline payload |
| `analysis` | object | yes | main OCR / analysis column | stable normalized payload for UI |

`analysis` object:

| Field | Type | Always present | Frontend usage | Notes |
| --- | --- | --- | --- | --- |
| `doc_type` | string | yes | document type badge | plugin-oriented type |
| `doc_type_confidence` | number \| null | yes | confidence chip | from detector classification |
| `classification_evidence` | object | yes | attachment-type label card | includes attachment label and confidence |
| `extracted_fields` | array | yes | field table | stable array form, good for React lists |
| `validation` | object | yes | validation issues summary | not business verification |
| `review` | object | yes | OCR risk / warnings area | pipeline review artifacts |
| `risk` | object | yes | small risk badge in analysis column | derived from current review state |
| `raw_artifacts` | object | yes | optional debug panel | do not bind critical UI to these keys |

`analysis.classification_evidence`:

| Field | Type | Usage |
| --- | --- | --- |
| `plugin` | string | original plugin route |
| `detector_doc_type` | string \| null | detector result |
| `ocr_backend` | string | debugging |
| `vlm_backend` | string | debugging |
| `attachment_label` | string | display in OCR / analysis column |
| `attachment_confidence` | number | display confidence |
| `matched_keywords` | string[] | explain why label was chosen |

`analysis.extracted_fields[]`:

| Field | Type | Usage |
| --- | --- | --- |
| `name` | string | field code / table key |
| `value` | any | field value |
| `confidence` | number \| null | optional confidence chip |
| `source` | string \| null | provenance |
| `bbox` | object \| null | future bbox overlay |
| `evidence_text` | string \| null | optional OCR snippet |
| `matched` | boolean | frontend emphasis / highlighting |

## 2. `POST /verify-attachment`

Business-facing verification endpoint.

Use it when the page needs:
- PASS / REVIEW / REJECT
- request-vs-document comparison
- rule list
- approval recommendation

### Request fields

| Field | Type | Required | Example | Frontend usage | Notes |
| --- | --- | --- | --- | --- | --- |
| `plugin_name` | string | yes* | `diagnosis_proof` | parser route | `plugin` alias accepted |
| `plugin` | string | no | `diagnosis_proof` | legacy alias only | prefer `plugin_name` |
| `file` | binary | yes | uploaded image/pdf bytes | attachment source | multipart file upload |
| `ocr_backend` | string | no | `mock` | debugging / override | optional |
| `vlm_backend` | string | no | `mock` | debugging / override | optional |
| `detector_backend` | string | no | `mock` | debugging / override | optional |
| `rectify_backend` | string | no | `mock` | debugging / override | optional |
| `failure_dir` | string | no | `data/failures` | backend persistence | usually omit |
| `expected_attachment_type` | string | conditional | `MEDICAL_CERTIFICATE` | direct expectation | accepted when a single attachment type is expected |
| `expected_attachment_types` | string or string[] | conditional | `BIRTH_CERTIFICATE,MARRIAGE_CERTIFICATE` | multi-expected type cases | current HTTP form path accepts CSV string |
| `leave_type` | string | conditional | `SICK` / `MARRIAGE` | business fallback | resolves expected attachment types via backend matrix |
| `applicant_name` | string | no | `张三` | business subject comparison | used by `applicant_name_match` |
| `related_person_name` | string | no | `李四` | relationship comparison | used by `related_person_match` |
| `related_person_relation` | string | no | `spouse` | explanation / UI display | currently evidence-only |
| `leave_start_date` | string | no | `2026-04-01` | date comparison | used by `leave_date_match` |
| `leave_end_date` | string | no | `2026-04-03` | date comparison | used by `leave_date_match` |
| arbitrary field overrides | string | no | `patient_name`, `registration_date` | parser assistance / demo injection | any non-reserved form field is forwarded into runner `fields` |

Conditional rule: at least one of `expected_attachment_type`, `expected_attachment_types`, or `leave_type` must be provided.

### Response fields

Top-level response:

| Field | Type | Always present | Frontend usage | Notes |
| --- | --- | --- | --- | --- |
| `filename` | string | yes | attachment card title | uploaded filename |
| `content_type` | string | yes | preview renderer selection | MIME type |
| `result` | object | yes | debug drawer | full low-level pipeline payload |
| `analysis` | object | yes | OCR / analysis column | same shape as `/analyze-document` |
| `verification` | object | yes | verification column | stable business-facing payload |

`verification` object:

| Field | Type | Always present | Frontend usage | Notes |
| --- | --- | --- | --- | --- |
| `verify_status` | `PASS` \| `REVIEW` \| `REJECT` | yes | summary badge / CTA state | primary decision |
| `risk_score` | number | yes | progress bar / badge | 0-100 |
| `risk_level` | `LOW` \| `MEDIUM` \| `HIGH` | yes | color-coded label | derived from score |
| `matched_attachment_type` | string | yes | verification summary | predicted attachment type |
| `extracted_fields` | object | yes | rule evidence panel | object form, keyed by field name |
| `rule_results` | array | yes | verification rule list | core approval-facing section |
| `warnings` | string[] | yes | summary alerts | failed rule messages |
| `evidence` | object | yes | request-vs-document comparison | includes request and classification snapshots |
| `needs_manual_review` | boolean | yes | footer CTA logic | true unless status is PASS |
| `summary_message` | string | yes | summary sentence | small header/subtitle |

`verification.rule_results[]`:

| Field | Type | Usage |
| --- | --- | --- |
| `rule_code` | string | stable rule identifier |
| `passed` | boolean | row state |
| `severity` | `info` \| `warning` \| `error` | badge / color |
| `score_delta` | number | explain risk contribution |
| `message` | string | user-facing explanation |
| `evidence` | object | row-level detail drawer |

`verification.evidence`:

| Field | Type | Usage |
| --- | --- | --- |
| `classification` | object | echo of analysis classification |
| `request` | object | original request snapshot plus resolved expected types |
| `fields` | object | extracted field map used by rules |

Important key for frontend debugging:
- `verification.evidence.request.resolved_expected_attachment_types`

## 3. Recommended frontend binding priorities

### Safe stable fields to bind first

From `/analyze-document`:
- `filename`
- `content_type`
- `analysis.doc_type`
- `analysis.doc_type_confidence`
- `analysis.classification_evidence.attachment_label`
- `analysis.classification_evidence.attachment_confidence`
- `analysis.classification_evidence.matched_keywords`
- `analysis.extracted_fields`
- `analysis.validation.accepted`
- `analysis.validation.issues`
- `analysis.review.decision`
- `analysis.review.warnings`
- `analysis.risk`

From `/verify-attachment`:
- `verification.verify_status`
- `verification.risk_score`
- `verification.risk_level`
- `verification.matched_attachment_type`
- `verification.rule_results`
- `verification.warnings`
- `verification.evidence.request`
- `verification.evidence.fields`
- `verification.needs_manual_review`
- `verification.summary_message`

### Fields that should stay in debug-only mode for now

- `result.detector`
- `result.rectify`
- `result.ocr`
- `result.vlm`
- `analysis.raw_artifacts`

## 4. Mock response files in this repo

See:

- `examples/mock-api/analyze-document.success.json`
- `examples/mock-api/analyze-document.boundary.partial-analysis.json`
- `examples/mock-api/analyze-document.error.missing-plugin.json`
- `examples/mock-api/verify-attachment.success.pass.json`
- `examples/mock-api/verify-attachment.boundary.review.json`
- `examples/mock-api/verify-attachment.boundary.reject.json`
- `examples/mock-api/verify-attachment.error.missing-expected.json`
- `examples/mock-ui/approval-verification-page.pass.json`
- `examples/mock-ui/approval-verification-page.review.json`

## 5. Current MVP scope to keep stable

Frontend demo scope for now:
- `SICK`
- `MARRIAGE`

Do not widen document coverage before this interface layer is stable.
