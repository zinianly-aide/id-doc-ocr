# Request ID Tracing Evidence

## Goal

Confirm whether a single case can be traced across:
- frontend UI
- frontend adapter request construction
- backend request handling and logs
- REVIEW / override operational records

This document records what is already confirmed, what is only partially confirmed, and what is still missing before pilot launch.

---

## 1. Expected tracing chain

Target pilot tracing chain:

upload
-> analyze
-> verify
-> REVIEW
-> override

Minimum audit expectation:
- one trace id should identify the case across technical logs and operational review records
- the approver or pilot support should be able to recover the same case later without guesswork

---

## 2. Confirmed implementation points

### 2.1 Frontend adapter generates / carries request_id

Confirmed by code inspection:
- file: `ui/approval-verification/src/adapters/realApprovalVerification.ts`
- `buildRequestId()` generates IDs like `LV-SICK-<uuid>`
- `analyzeDocumentReal()` sets `formData.request_id`
- `verifyAttachmentReal()` reuses the current request_id and sets `formData.request_id`

Observed by browser fetch interception on V1 page:
- analyze request form data carried `LV-SICK-1cbd7598-bc04-4e64-87c8-45b838f0eacd`
- verify request form data carried the same `LV-SICK-1cbd7598-bc04-4e64-87c8-45b838f0eacd`

Conclusion:
- adapter-level request_id continuity between analyze and verify is confirmed

### 2.2 Backend accepts and echoes request_id

Confirmed by code inspection:
- file: `src/id_doc_ocr/service/app.py`
- `_resolve_request_id()` reads request_id from form or header
- response payload includes `request_id`
- `_attach_request_id()` adds `X-Request-Id` header
- `_log_stage()` logs `request_id` in analyze/verify input and result stages

Confirmed by direct API evidence against local validation backend on `127.0.0.1:8014`:
- `/analyze-document` returned header and body request_id = `TRACE-LAUNCH-ANALYZE-001`
- `/verify-attachment` returned header and body request_id = `TRACE-LAUNCH-VERIFY-001`

Conclusion:
- backend request_id echo in successful responses is confirmed

### 2.3 Backend log trace is operational

Evidence captured from local validation backend log file `/tmp/id_doc_ocr_trace.log`:
- `analyze_input request_id=TRACE-LAUNCH-ANALYZE-001 ...`
- `analyze_result request_id=TRACE-LAUNCH-ANALYZE-001 ...`
- `request method=POST path=/analyze-document ... request_id=TRACE-LAUNCH-ANALYZE-001`
- `verify_input request_id=TRACE-LAUNCH-VERIFY-001 ...`
- `verify_result request_id=TRACE-LAUNCH-VERIFY-001 ...`
- `request method=POST path=/verify-attachment ... request_id=TRACE-LAUNCH-VERIFY-001`

Conclusion:
- backend log traceability is confirmed on the local validation backend

---

## 3. Observed tracing gaps

### 3.1 Frontend UI requestId display is not updated to the real adapter request_id

Observed on the V1 page:
- visible request header still showed mock request ids like `REQ-2026-0424-001`
- actual fetch form data used generated ids like `LV-SICK-<uuid>`

Impact:
- approver-visible request id is currently not the same as the real request id used in backend requests
- screenshot-based incident reporting may point to the wrong identifier

Severity:
- High

Recommendation:
- bind visible request header requestId to the real request lifecycle once analyze/verify starts
- do not keep static mock requestId after real adapter calls succeed or fail

### 3.2 Frontend fetch wrapper could not read response `X-Request-Id`

Observed in browser instrumentation:
- request form data carried request_id correctly
- `response.headers.get('x-request-id')` returned `null` for live browser fetches to `http://127.0.0.1:8000`

Possible causes:
- response header may exist on the wire but is not exposed via CORS
- or the current browser environment is not surfacing it to JS

Impact:
- frontend cannot independently verify the backend-echoed request id from the response header
- this weakens end-to-end evidence gathering from the browser alone

Severity:
- Medium

Recommendation:
- verify whether `Access-Control-Expose-Headers: X-Request-Id` is present in the real pilot path
- if not, expose it before launch

### 3.3 Some backend failure responses do not carry request_id

Observed by direct API calls:
- invalid verify payload (`422`) returned no request_id in header/body
- empty upload (`400 Uploaded file is empty`) returned no request_id in header/body

Impact:
- failure cases can become untraceable exactly when operators most need audit evidence

Severity:
- Medium

Recommendation:
- decide whether all business-handled 4xx error responses should also carry request_id
- especially important for pilot support, failure-state review, and weekly incident analysis

### 3.4 REVIEW and override linkage is only process-defined, not product-enforced

Current state:
- `docs/review-sop.md` and `docs/pilot-metrics.md` define request_id / case id usage for override and risk ledger
- the product UI itself does not currently expose a built-in review ledger or override audit record flow

Impact:
- traceability from verify -> REVIEW -> override depends on disciplined operations rather than system enforcement

Severity:
- High for launch governance, though not a core algorithm bug

Recommendation:
- before pilot launch, freeze one external ledger / issue tracker template where request_id is mandatory for REVIEW and override records
- treat this as a launch blocker if the team cannot commit to one source of truth

---

## 4. What is currently traceable vs not traceable

| Link in chain | Status | Evidence |
|---|---|---|
| adapter-generated request_id | Confirmed | code + browser fetch interception |
| analyze request form carries request_id | Confirmed | browser fetch interception |
| verify request form carries same request_id | Confirmed | browser fetch interception |
| backend successful response echoes request_id | Confirmed | direct API calls |
| backend log contains request_id | Confirmed | `/tmp/id_doc_ocr_trace.log` |
| visible frontend header matches real runtime request_id | Not confirmed; currently mismatched | browser UI still shows mock request id |
| frontend JS can read response `X-Request-Id` | Not confirmed | fetch interception returned null |
| REVIEW record includes request_id by system design | Process-defined only | documented, not enforced in UI |
| override record includes request_id by system design | Process-defined only | documented, not enforced in UI |

---

## 5. Launch judgment

Current request_id tracing judgment:
- technically viable at adapter + backend + backend log layers
- not yet launch-complete at operator-visible UI + review-ledger + override-audit layers

Go / no-go implication:
- do not call request tracing “fully confirmed” yet
- current status should be recorded as `Partially confirmed`

Minimum launch actions still needed:
1. make UI-visible requestId align with the real request lifecycle
2. confirm frontend can read or otherwise preserve backend response request_id
3. ensure failure responses also carry request_id, or explicitly accept that risk
4. freeze an external review / override ledger template with mandatory request_id field

---

## 6. Final conclusion

Current state is good enough to say:
- the system is not missing request_id plumbing entirely
- the backend path is traceable
- the adapter path is traceable

Current state is not yet good enough to say:
- the pilot is end-to-end auditable from approver screenshot to override ledger without extra manual discipline

Therefore, request_id traceability is a remaining launch blocker, not a solved item.
