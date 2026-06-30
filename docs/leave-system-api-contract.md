# Leave System API Contract Template

## Purpose

This document is the working contract template for the real leave-system sandbox integration. It records the exact pending, attachment download, and callback interfaces used by the `leave_audit` sidecar before enabling real callback writeback.

## Scope

- Integration mode: sidecar audit; the leave system remains the source of truth.
- Adapter mode: `ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http`.
- First sandbox phase: pending + download + OCR/verify + callback dry-run payload review.
- Real callback writeback is allowed only after the dry-run payload is confirmed by the leave-system owner.

## Environment Variables

```bash
export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http
export ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL=https://leave-system-sandbox.example.com
export ID_DOC_OCR_LEAVE_SYSTEM_TOKEN=replace-me
export ID_DOC_OCR_LEAVE_SYSTEM_PENDING_API=/api/leave/attachments/pending
export ID_DOC_OCR_LEAVE_SYSTEM_DOWNLOAD_API=/api/leave/attachments/{attachment_id}/download
export ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_API=/api/leave/audit-result
export ID_DOC_OCR_LEAVE_SYSTEM_TIMEOUT_SECONDS=10
export ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE=configs/leave_system_field_mapping.yaml
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true
export ID_DOC_OCR_LEAVE_AUDIT_DB=.local/leave_audit.db
```

## Authentication

### Current sandbox assumption

- Method: Bearer token
- Header: `Authorization: Bearer <token>`
- Token source: `ID_DOC_OCR_LEAVE_SYSTEM_TOKEN`

### Items to confirm with leave-system owner

| Item | Expected | Confirmed Value | Notes |
| --- | --- | --- | --- |
| Auth scheme | Bearer token | TBD | Confirm whether extra headers are required |
| Token expiry | TBD | TBD | Confirm rotation cadence |
| IP allowlist | TBD | TBD | Confirm sandbox caller IP constraints |
| User/tenant header | Not required by default | TBD | Add only if sandbox requires it |

## 1. Pending API

### Purpose

Fetch leave requests with attachments that need sidecar OCR and verification.

### Request

```http
GET {ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL}{ID_DOC_OCR_LEAVE_SYSTEM_PENDING_API}
Authorization: Bearer <token>
Accept: application/json
```

### Expected response shape

The adapter accepts either a direct list or an object containing `tasks` or `data`.

```json
{
  "tasks": [
    {
      "applyNo": "LR-20260523-000001",
      "empNo": "E001",
      "empName": "张三",
      "absenceType": "SICK",
      "startTime": "2026-05-23 09:00:00",
      "endTime": "2026-05-25 18:00:00",
      "attachments": [
        {
          "fileId": "FILE-001",
          "fileName": "diagnosis.jpg",
          "fileUrl": "https://leave-system-sandbox.example.com/files/FILE-001",
          "pluginName": "diagnosis_proof"
        }
      ]
    }
  ]
}
```

### Internal canonical fields

| Internal field | Required | Description |
| --- | --- | --- |
| `request_id` | Optional | Sidecar request id; falls back to `leave_request_id` if absent |
| `leave_request_id` | Yes | Leave-system request/application id |
| `employee_id` | Optional | Employee id or number |
| `employee_name` | Yes | Applicant/employee display name |
| `leave_type` | Yes | Leave type, e.g. `SICK`, `MARRIAGE` |
| `leave_start_date` | Optional | Leave start date/time |
| `leave_end_date` | Optional | Leave end date/time |
| `attachments[].attachment_id` | Yes | Attachment/file id |
| `attachments[].attachment_name` | Optional | Attachment display filename |
| `attachments[].attachment_url` | Yes | Download URL or adapter-specific file key |
| `attachments[].plugin_name` | Optional | Preferred OCR plugin name |

### Field mapping

Use `configs/leave_system_field_mapping.yaml` first. If sandbox returns fields not covered by the default mapping, add aliases in the config or set `ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE` to a sandbox-specific mapping file.

Default examples:

| Internal field | External aliases |
| --- | --- |
| `leave_request_id` | `leave_request_id`, `leaveRequestId`, `applyNo`, `requestNo` |
| `employee_id` | `employee_id`, `employeeId`, `empNo` |
| `employee_name` | `employee_name`, `employeeName`, `empName` |
| `leave_type` | `leave_type`, `leaveType`, `absenceType` |
| `leave_start_date` | `leave_start_date`, `leaveStartDate`, `startDate`, `startTime` |
| `leave_end_date` | `leave_end_date`, `leaveEndDate`, `endDate`, `endTime` |
| `attachment_id` | `attachment_id`, `attachmentId`, `fileId` |
| `attachment_name` | `attachment_name`, `attachmentName`, `fileName` |
| `attachment_url` | `attachment_url`, `attachmentUrl`, `fileUrl` |
| `plugin_name` | `plugin_name`, `pluginName` |

Do not change `HttpLeaveSystemAdapter` for field-name differences unless mapping cannot express the difference.

## 2. Attachment Download API

### Purpose

Download the attachment bytes for OCR.

### Request mode A: direct URL

If `attachment_url` starts with `http://` or `https://`, the adapter directly requests that URL.

```http
GET {attachment_url}
Authorization: Bearer <token>
```

### Request mode B: configured download API

If `attachment_url` is not an absolute URL, the adapter calls the configured download API with `attachment_url` as a query parameter.

```http
GET {ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL}{ID_DOC_OCR_LEAVE_SYSTEM_DOWNLOAD_API}?attachment_url=<attachment_url>
Authorization: Bearer <token>
```

### Expected response

- Body: raw file bytes
- Successful status: 2xx
- Recommended headers:
  - `Content-Type: image/jpeg`, `image/png`, `application/pdf`, or other real MIME type
  - `Content-Length: <bytes>` when available

### Items to confirm

| Item | Expected | Confirmed Value | Notes |
| --- | --- | --- | --- |
| Direct URL allowed | TBD | TBD | If no, use configured download API |
| Download auth | Same Bearer token | TBD | Confirm if file service uses separate token |
| Max file size | TBD | TBD | Record large attachment behavior |
| Supported file types | image/jpeg, image/png, application/pdf | TBD | PDF bytes are rendered page-by-page before OCR; multi-page PDFs are supported |

## 3. Callback API

### Purpose

Write OCR/verification result back to the leave system after dry-run confirmation.

### Dry-run safety rule

When `ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true`, the sidecar does not call the real callback API. It returns and persists the would-be payload for inspection.

### Real request

```http
POST {ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL}{ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_API}
Authorization: Bearer <token>
Content-Type: application/json
```

### Current callback payload

```json
{
  "request_id": "LR-20260523-000001",
  "leave_request_id": "LR-20260523-000001",
  "verify_status": "REVIEW",
  "risk_level": "MEDIUM",
  "risk_score": 45,
  "needs_manual_review": true,
  "summary": "REVIEW: needs HR review",
  "rule_results": [
    {
      "rule_code": "applicant_name_match",
      "passed": false,
      "severity": "warning",
      "display_message": "申请人与材料中的人员信息不一致"
    }
  ]
}
```

### Callback fields to confirm

| Current field | Required by sidecar | Leave-system target field | Confirmed? | Notes |
| --- | --- | --- | --- | --- |
| `request_id` | Yes | TBD | No | Sidecar trace id / fallback request id |
| `leave_request_id` | Yes | TBD | No | Leave-system application id |
| `verify_status` | Yes | TBD | No | `PASS` / `REVIEW` / `REJECT` |
| `risk_level` | Optional | TBD | No | `LOW` / `MEDIUM` / `HIGH` |
| `risk_score` | Optional | TBD | No | Numeric risk score |
| `needs_manual_review` | Optional | TBD | No | Boolean |
| `summary` | Optional | TBD | No | Human-readable result summary |
| `rule_results` | Optional | TBD | No | Detailed rule evidence |

If callback target field names differ, see `docs/callback-field-mapping-design.md`. Do not implement ad-hoc payload changes in the HTTP adapter until the callback contract is confirmed.

## 4. Error Codes

### Upstream pending/download/callback errors

| HTTP status | Meaning | Sidecar handling | Required sandbox note |
| --- | --- | --- | --- |
| 400 | Bad request / invalid params | Raise `LeaveSystemHttpError` with body preview | Record request params and response body |
| 401 | Missing/invalid auth | Raise `LeaveSystemHttpError` | Confirm token/header |
| 403 | Forbidden / no permission | Raise `LeaveSystemHttpError` | Confirm allowlist/permission |
| 404 | Endpoint or file not found | Raise `LeaveSystemHttpError` | Confirm URL/path and attachment id |
| 408/504 | Timeout | Request fails through httpx/HTTP error path | Record elapsed time and retry policy |
| 429 | Rate limited | Raise `LeaveSystemHttpError` | Confirm backoff window |
| 5xx | Upstream unavailable | Raise `LeaveSystemHttpError` | Record body preview and incident id if any |

### Payload/mapping errors

| Error | Meaning | Action |
| --- | --- | --- |
| `pending response must be a list or contain tasks/data list` | Response envelope is unsupported | Confirm pending response shape |
| `missing required field '<field>'` | Required task field could not be mapped | Add alias to mapping file or fix upstream payload |
| `missing required attachment field '<field>'` | Required attachment field could not be mapped | Add alias to mapping file or fix upstream payload |

## 5. Timeout and Retry Agreement

### Current sidecar behavior

- `ID_DOC_OCR_LEAVE_SYSTEM_TIMEOUT_SECONDS` controls HTTP client timeout; default `10` seconds.
- The HTTP adapter does not currently perform automatic retries.
- Retry/replay should be controlled at the pilot operations level until the sandbox contract confirms idempotency.

### To confirm before real pilot

| Topic | Proposed agreement | Confirmed Value |
| --- | --- | --- |
| Pending timeout | 10 seconds | TBD |
| Download timeout | 10 seconds; may increase for large files if needed | TBD |
| Callback timeout | 10 seconds | TBD |
| Retry policy | No automatic retry in first sandbox; manual replay by request_id | TBD |
| Callback idempotency key | `request_id` or `leave_request_id` | TBD |
| Duplicate callback behavior | Upsert latest result or reject duplicate | TBD |

## 6. Sandbox Evidence Checklist

For each sandbox session, copy the final values into `docs/sandbox-integration-log.md`:

- pending raw response sample
- field mapping table: original field -> internal field -> configured? -> code change needed?
- attachment download status and file metadata
- OCR/verify result
- callback dry-run payload
- real callback writeback result after dry-run signoff
- error codes and retry observations
