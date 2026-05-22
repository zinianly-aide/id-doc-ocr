# Callback Field Mapping Design

## Purpose

This is a design note only. It reserves a future configuration-based callback payload mapping layer for the real leave-system sandbox if callback target field names differ from the current sidecar payload.

No code is implemented in this step.

## Current Callback Payload

The current callback payload is produced by `AuditService` / `HttpLeaveSystemAdapter` and contains:

```json
{
  "request_id": "LR-20260523-000001",
  "leave_request_id": "LR-20260523-000001",
  "verify_status": "REVIEW",
  "risk_level": "MEDIUM",
  "risk_score": 45,
  "needs_manual_review": true,
  "summary": "REVIEW: needs HR review",
  "rule_results": []
}
```

This shape should remain the internal canonical callback contract.

## Problem to Solve Later

Different leave systems may require callback fields such as:

| Internal field | Possible external field |
| --- | --- |
| `leave_request_id` | `applyNo`, `requestNo`, `leaveRequestId` |
| `verify_status` | `auditResult`, `verifyStatus`, `checkStatus` |
| `risk_level` | `riskLevel`, `riskGrade` |
| `risk_score` | `riskScore`, `score` |
| `needs_manual_review` | `manualReviewRequired`, `needReview` |
| `summary` | `auditSummary`, `remark`, `comment` |
| `rule_results` | `details`, `ruleResults`, `evidenceList` |

If this happens, avoid hardcoding a one-off payload inside `HttpLeaveSystemAdapter`.

## Proposed Future Configuration

Potential file:

```text
configs/leave_system_callback_mapping.yaml
```

Potential env var:

```bash
ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_MAPPING_FILE=configs/leave_system_callback_mapping.yaml
```

Potential config shape:

```yaml
request_id: requestId
leave_request_id: applyNo
verify_status: auditResult
risk_level: riskLevel
risk_score: riskScore
needs_manual_review: needReview
summary: auditSummary
rule_results: ruleResults
status_values:
  PASS: APPROVED
  REVIEW: MANUAL_REVIEW
  REJECT: REJECTED
```

## Proposed Mapping Rules

1. Keep the canonical internal payload unchanged.
2. Apply callback mapping only at the adapter boundary before HTTP POST.
3. Support field renaming first; do not add expression language unless required.
4. Support status value mapping for `PASS` / `REVIEW` / `REJECT`.
5. Preserve raw canonical payload in dry-run metadata for auditability.
6. Include mapped payload in dry-run metadata so the leave-system owner can approve the exact writeback body.

## Proposed Dry-Run Response Extension

Future dry-run response can include both payloads:

```json
{
  "dry_run": true,
  "callback_skipped": true,
  "callback_payload": {
    "request_id": "LR-20260523-000001",
    "leave_request_id": "LR-20260523-000001",
    "verify_status": "REVIEW"
  },
  "mapped_callback_payload": {
    "requestId": "LR-20260523-000001",
    "applyNo": "LR-20260523-000001",
    "auditResult": "MANUAL_REVIEW"
  }
}
```

## Non-Goals for the Current Sandbox Readiness Step

- Do not implement callback mapping code yet.
- Do not change current callback payload names until the leave-system owner confirms the target contract.
- Do not add callback retries until idempotency and duplicate handling are confirmed.
- Do not mix pending field mapping and callback field mapping in the same config file unless the future contract review explicitly chooses that approach.

## Acceptance Criteria Before Implementation

Implement callback mapping only after all are true:

1. Leave-system owner confirms callback target field names.
2. Dry-run payload comparison shows canonical payload does not match target field names.
3. A mapping config format is approved.
4. Tests are added for field rename and status value mapping.
5. Dry-run response shows both canonical and mapped payloads.
