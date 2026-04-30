# Pilot Contract v1

## Status
- Status flow: `Draft -> Candidate -> Confirmed`
- Current status: `Confirmed（试点正式可用版本）`
- Version: `v1`

## Background

The project already has a usable approval-verification chain:

- `/analyze-document`
- `/verify-attachment`
- approval verification UI
- mock / real adapter mode
- pilot governance documents

However, a business pilot cannot start safely until the integration contract is frozen.

Without a frozen contract:
- the leave system and verification service may interpret fields differently,
- REVIEW / PASS / REJECT may be used inconsistently,
- error handling and fallback behavior may drift,
- pilot metrics and issue tracking cannot be standardized.

This document freezes the pilot integration contract for the first business pilot window.

## Goal

Freeze the pilot integration boundary between the leave-approval system and the approval-verification capability so that:

1. business input semantics are explicit,
2. output fields are stable enough for pilot use,
3. REVIEW / PASS / REJECT have consistent business meaning,
4. error handling and manual fallback are governed,
5. the pilot can run with low scope drift and clear traceability.

## Scope

### In Scope

- Pilot integration for leave attachment verification
- Business scenarios:
  - `SICK`
  - `MARRIAGE`
- Single attachment, single image upload
- Approval-assistance only
- Human final decision retained
- Contract for request fields, response fields, status semantics, error codes, timeout, retry, and fallback

### Out of Scope

- PDF support
- Multi-attachment aggregation
- Automatic approval / automatic rejection
- Company-wide rollout contract
- Broad generalized document-type expansion beyond current pilot scope
- Non-pilot technical debug payloads as stable business contract

## Time Plan

| Phase | Purpose | Output |
|---|---|---|
| Current phase | freeze pilot contract v1 | this document |
| Next phase | connect leave system sandbox using v1 | integration validation evidence |
| Pilot phase | use v1 as the only accepted pilot integration contract | operational pilot data |

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

## 1. 为什么要冻结 contract

The contract must be frozen now because it is the upstream dependency for all of the following:

- leave-system sandbox integration
- pilot UI display consistency
- error and retry governance
- pilot SOPs
- metrics collection
- management approval for pilot launch

If the contract is not frozen first, every downstream workstream will re-open the same field-definition debate.

## 2. 接入范围

### 当前支持什么

The v1 pilot contract supports only:

- leave scenarios:
  - `SICK`
  - `MARRIAGE`
- single attachment
- single image file
- request-vs-document verification through `/verify-attachment`
- approval-facing outputs:
  - `PASS`
  - `REVIEW`
  - `REJECT`
- manual fallback and review-first operation mode

### 当前明确不支持什么

The v1 pilot contract does not support:

- PDF
- multiple attachments in one request
- batch verification
- automatic approval execution
- automatic rejection execution
- business commitment on non-pilot attachment categories
- UI or workflow assumptions based on debug-only low-level OCR artifacts

## 3. 请求字段

### Endpoint

- `POST /verify-attachment`

### Request format

- `multipart/form-data`

### Required and optional request fields

| Field | Type | Required | Example | Business meaning | Rule |
|---|---|---:|---|---|---|
| `leave_type` | string | Yes* | `SICK`, `MARRIAGE` | leave scenario used to resolve expected attachment type(s) | required for v1 pilot unless explicit expected type extension is approved later |
| `applicant_name` | string | Yes | `张三` | employee / applicant name from leave request | used in subject matching rules |
| `related_person_name` | string | Conditional | `李四` | related person from leave request | required for `MARRIAGE`; omitted for `SICK` |
| `related_person_relation` | string | Conditional | `spouse` | relationship type in leave request | required for `MARRIAGE`; omitted for `SICK` |
| `leave_start_date` | string (`YYYY-MM-DD`) | Yes | `2026-04-01` | leave start date from leave request | used in date comparison rules |
| `leave_end_date` | string (`YYYY-MM-DD`) | Yes | `2026-04-03` | leave end date from leave request | used in date comparison rules |
| `file` | binary | Yes | image upload | attachment being verified | single image only in v1 |
| `plugin_name` | string | Yes | `diagnosis_proof`, `marriage_certificate` | parser route for current pilot | required in current service contract |
| `ocr_backend` | string | No | `mock`, `paddleocr` | runtime override for controlled environments | optional; normally omitted in business integration |
| `vlm_backend` | string | No | `mock` | runtime override for controlled environments | optional |
| `detector_backend` | string | No | `pil` | runtime override for controlled environments | optional |
| `rectify_backend` | string | No | `pil` | runtime override for controlled environments | optional |

`*` For the v1 pilot, `leave_type` is treated as mandatory business input even though the lower-level service can accept other expected-type patterns.

### Leave-type-specific requirements

| leave_type | Additional required fields |
|---|---|
| `SICK` | none beyond common required fields |
| `MARRIAGE` | `related_person_name`, `related_person_relation=spouse` |

### Request validation rules

1. `file` must be a single image file.
2. `leave_start_date` and `leave_end_date` must use `YYYY-MM-DD` format.
3. `leave_start_date` must not be later than `leave_end_date`.
4. `MARRIAGE` requires relationship context.
5. Unknown or unsupported `leave_type` is rejected at contract validation stage.

## 4. 响应字段

### Response contract level

For the pilot, the integration response must include a stable top-level envelope. If the core service does not natively emit a field such as `request_id`, the integration layer or gateway must inject and echo it.

### Response fields

| Field | Type | Required | Example | Meaning | Notes |
|---|---|---:|---|---|---|
| `request_id` | string | Yes | `LV-VERIFY-2026-000123` | end-to-end trace ID for pilot case tracking | generated by caller or integration layer, must be echoed back |
| `verify_status` | enum | Yes | `PASS`, `REVIEW`, `REJECT` | approval-facing verification result | primary business result |
| `risk_level` | enum | Yes | `LOW`, `MEDIUM`, `HIGH` | risk category for business use | derived from risk score |
| `risk_score` | integer | Yes | `0`, `31`, `75` | verification risk score | used for sorting, reporting, and threshold checks |
| `matched_attachment_type` | string | Yes | `MEDICAL_CERTIFICATE`, `MARRIAGE_CERTIFICATE` | system-recognized attachment category | must align with pilot scenario expectation |
| `summary_message` | string | Yes | `PASS: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']` | compact decision explanation | approval page summary sentence |
| `warnings` | string[] | Yes | `[]`, `["related person does not match extracted document relationship party"]` | verification warnings for business review | must be readable by approvers |
| `rule_results` | array | Yes | see below | rule-by-rule verification output | approval-facing explainability section |
| `needs_manual_review` | boolean | Yes | `false`, `true` | whether the case should be manually reviewed | in v1, all non-PASS cases should be true |

### `rule_results` item fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `rule_code` | string | Yes | stable rule identifier |
| `passed` | boolean | Yes | whether this rule passed |
| `severity` | enum | Yes | `info`, `warning`, `error` |
| `score_delta` | integer | Yes | risk contribution of this rule |
| `message` | string | Yes | approver-facing explanation |
| `evidence` | object | No | optional row-level detail |

### Business contract note

The full service response may still contain `analysis`, `verification`, and `result`, but the pilot business contract freezes the fields above as the minimum stable integration output set.

## 5. 状态语义

### PASS

Definition:
- the attachment type matches the leave scenario expectation,
- critical business rules did not produce a blocking issue,
- the system does not require manual review under the v1 rule set.

Business action recommendation:
- approver may proceed with normal approval review,
- no additional attachment re-check is required by default,
- human approver still retains final approval authority.

### REVIEW

Definition:
- the attachment is not clearly invalid,
- but uncertainty, mismatch, weak evidence, or missing critical business confidence prevents direct release.

Business action recommendation:
- send to manual review,
- approver should inspect warnings, rule results, and request-vs-document evidence,
- do not treat REVIEW as approval-ready.

### REJECT

Definition:
- the attachment is materially inconsistent with the leave request,
- or the rule result indicates the material should not be accepted as the required evidence.

Business action recommendation:
- approver should treat the attachment as not acceptable in its current state,
- typically request correction, replacement, or business rejection according to policy,
- human approver still confirms the final business action.

## 6. 错误码规范

The pilot contract uses stable business-facing error codes. The integration layer should normalize lower-level failures into the following set.

| Error Code | When to use | HTTP suggestion | Business handling |
|---|---|---:|---|
| `CONTRACT_VALIDATION_ERROR` | missing required business fields, bad date format, invalid leave-type usage | 422 | fix request payload before retry |
| `UNSUPPORTED_FILE_TYPE` | uploaded file is not an allowed image type for v1 pilot | 415 | ask user to upload supported image format |
| `EMPTY_FILE` | upload is empty or unreadable as a payload | 400 | ask user to re-upload |
| `UNKNOWN_PLUGIN` | integration sent unsupported parser route | 404 or 422 | integration defect, not approver action |
| `OCR_TIMEOUT` | OCR / processing exceeds agreed timeout budget | 504 | safe to retry under retry policy |
| `BACKEND_UNAVAILABLE` | configured OCR / VLM / detector backend is unavailable | 503 | retry or switch to manual fallback |
| `VERIFICATION_RUNTIME_ERROR` | service failed during verification logic execution | 500 | log, trace by request_id, use manual fallback |
| `INTERNAL_ERROR` | uncategorized service failure | 500 | use manual fallback and escalate |

### Error response recommendation

The pilot integration layer should return at least:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `request_id` | string | Yes | trace ID |
| `error_code` | string | Yes | normalized contract error code |
| `message` | string | Yes | readable error summary |
| `retryable` | boolean | Yes | whether retry is recommended |

## 7. 超时与重试建议

### Timeout recommendation

| Flow | Suggested timeout |
|---|---:|
| client to integration gateway | 10s |
| integration to verification service | 8s |
| end-to-end approver-visible target | under 8s at P95 |

### Retry recommendation

Retry allowed:
- `OCR_TIMEOUT`
- `BACKEND_UNAVAILABLE`
- temporary network errors

Retry not allowed without payload correction:
- `CONTRACT_VALIDATION_ERROR`
- `UNSUPPORTED_FILE_TYPE`
- `EMPTY_FILE`

Suggested retry policy:
- maximum 1 automatic retry for retryable technical failures
- if still failing, return visible error and route to manual fallback
- do not loop retries silently in the approval UI

## 8. 人工兜底机制

The pilot operates under a strict human-fallback rule.

### Mandatory fallback situations

Manual fallback must be used when:
1. verification request returns a normalized error,
2. the system returns `REVIEW`,
3. the service cannot produce a valid business result in time,
4. business users do not trust the returned result for the case.

### UI behavior expectation

When a technical failure occurs:
- show the error clearly,
- if an older result is displayed, label it as reference-only,
- do not allow the user to mistake stale output for the latest verification conclusion.

### Governance principle

During the pilot:
- the tool assists approval,
- the tool does not replace approval responsibility,
- final responsibility remains with the human approver and business process owner.

## 9. Versioning

- Current version: `v1`
- Scope: first small-scope business pilot only
- Change policy:
  - non-breaking clarifications may update the document while keeping `v1`
  - any field-level or semantic breaking change requires `v2`

## Risks

| Risk | Description | Control |
|---|---|---|
| Contract drift | business and engineering interpret fields differently | this document is the single pilot contract source of truth |
| Service / integration mismatch | core service fields and pilot envelope are not perfectly aligned | integration layer must normalize and echo required pilot fields |
| Over-expansion | teams try to add PDF / multi-attachment too early | explicitly out of scope for v1 |
| Semantic misuse | REVIEW / PASS / REJECT used inconsistently by approvers | business actions are frozen in this document |

## Acceptance Standard

This contract is considered frozen enough for pilot integration only if:

1. business owner accepts the v1 field set,
2. HR accepts the REVIEW / PASS / REJECT semantics,
3. engineering accepts the top-level response envelope,
4. QA can write integration checks directly from this document,
5. pilot kickoff uses this document as the only contract reference.

## Next Action Items

1. Review and approve `docs/contract-pilot-v1.md` with business, HR, product, backend, frontend, and QA.
2. Use this contract to prepare the leave-system sandbox integration checklist.
3. Build `docs/METRICS.md` and `docs/RISKS.md` using the frozen contract language.
4. Start P2 by defining the SICK pilot sample set and readiness baseline against this v1 contract.
