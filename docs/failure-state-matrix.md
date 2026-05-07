# Approval Verification Failure-State Matrix

## Purpose

This document records the current failure-state validation status for approval-verification before pilot traffic starts.

Scope of this round:
- UI stability checks on the V1 debug page at `http://127.0.0.1:4173/`
- direct API checks against local backend validation service
- emphasis on stale state, fallback safety, request traceability, and false-PASS prevention

Evidence basis used in this round:
- browser-driven V1 page rehearsal in real-adapter mode
- targeted backend regression tests
- direct API calls against local backend instances on `127.0.0.1:8000` and `127.0.0.1:8014`

Status legend:
- Pass = expected behavior observed
- Partial = some safe behavior exists, but there is a traceability or UX gap
- Fail = unsafe or misleading behavior observed
- Not yet validated = no direct evidence collected in this round

---

## A. Analyze-stage failures

| Case | Trigger | Expected behavior | Actual behavior | Current status | Risk level | Owner | Follow-up action |
|---|---|---|---|---|---|---|---|
| analyze fail | V1 `Enable analyze error demo` + `Run API demo analyze` | loading ends, analyze error shown, old analysis marked stale, approver not misled | Observed. `analyzeStatus=error`; explicit error copy shown; old analysis card remains with clear “旧结果/仅供参考” warning | Pass | Medium | Frontend Engineer | Keep as regression rehearsal case |
| analyze timeout | not directly simulated as timeout; network-fail pattern exercised instead | loading ends, error visible, no silent hang | No dedicated timeout harness used; behavior inferred from simulated fetch failure only | Not yet validated | Medium | Frontend Engineer + Backend Engineer | Add explicit timeout rehearsal or fetch-abort drill before launch |
| invalid payload | direct API: `/verify-attachment` without expected attachment / leave_type | server should reject clearly and not return misleading success payload | Observed `422 expected_attachment_type is required`; no request_id returned in error response | Partial | Medium | Backend Engineer | Decide whether 4xx error responses should also carry request_id for audit continuity |
| backend unavailable during analyze | can be simulated by fetch rejection on analyze path | error shown, loading ends, old result marked stale, manual fallback clear | No dedicated analyze-path backend-down drill captured in this round; verify-path backend-down was captured | Not yet validated | High | Frontend Engineer | Run explicit analyze-path backend-down rehearsal before go/no-go |
| malformed analyze response | fetch monkeypatch returns `200 not-json` for `/analyze-document` | UI should fail closed, show parse error, preserve old result as stale only | Observed parse error; stale analysis warning shown; loading ended | Pass | Medium | Frontend Engineer | Keep as regression rehearsal case |

---

## B. Verify-stage failures

| Case | Trigger | Expected behavior | Actual behavior | Current status | Risk level | Owner | Follow-up action |
|---|---|---|---|---|---|---|---|
| verify fail | V1 `Enable verify error demo` + `Run API demo verify` | loading ends, verify error shown, old verify result explicitly marked reference-only | Observed. `verifyStatus=error`; explicit error copy shown; old verify card remains with “上一次核验结果，仅供参考” warning | Pass | Medium | Frontend Engineer | Keep as regression rehearsal case |
| stale result after verify fail | successful prior result then verify error | old result may remain, but must be unmistakably stale and not approval-ready | Observed. Old PASS/REVIEW result remains, but warning copy clearly says not to approve from it | Pass | High | Frontend Engineer + QA | Include screenshot/evidence in launch pack |
| repeated verify click | slow verify simulation + repeated click attempt | second click blocked during loading; no duplicate submission | Observed. Button became `Verifying...` and `disabled=true` while pending | Pass | Low | Frontend Engineer | Keep as regression rehearsal case |
| partial verify response | fetch monkeypatch returns incomplete JSON for `/verify-attachment` | UI should fail closed with clear error and preserve stale result only | Observed failure: `Cannot read properties of undefined (reading 'doc_type')`; stale verify warning shown; loading ended | Partial | High | Frontend Engineer | Convert builder error into clearer user-facing guardrail; keep fail-closed behavior |
| malformed verify response | not separately isolated from partial; simulated backend unavailable instead | UI should fail closed and not enter half-rendered state | No dedicated malformed JSON verify drill captured in this round | Not yet validated | Medium | Frontend Engineer | Add verify malformed-JSON rehearsal before launch |
| network disconnect / backend unavailable during verify | fetch monkeypatch throws `TypeError('simulated backend unavailable')` on `/verify-attachment` | explicit error, loading ends, stale result clearly marked, no silent fallback to success | Observed. `verifyStatus=error`; stale verify warning shown; old PASS preserved as reference only | Pass | High | Frontend Engineer + Backend Engineer | Keep as launch evidence |

---

## C. Upload-stage failures

| Case | Trigger | Expected behavior | Actual behavior | Current status | Risk level | Owner | Follow-up action |
|---|---|---|---|---|---|---|---|
| non-image upload | synthetic `text/plain` file selected in V1 | request blocked client-side; user sees clear error; old result not treated as new result | Observed. File rejected with `当前仅支持 image/*...`; analyze/verify errors set; old results clearly marked stale | Pass | Medium | Frontend Engineer | Keep as launch evidence |
| empty file | direct API with zero-byte `image/jpeg` | backend rejects clearly; UI should later surface it clearly | Direct API observed `400 Uploaded file is empty`; UI path not directly exercised | Partial | Medium | Backend Engineer + Frontend Engineer | Add UI rehearsal for empty image file |
| unsupported mime | synthetic `text/plain` file | blocked client-side before request | Observed via non-image upload drill | Pass | Low | Frontend Engineer | No extra action beyond regression note |
| corrupted image | synthetic `image/jpeg` file with invalid bytes | should fail closed, typically REVIEW/REJECT, not PASS | Observed. Analyze returned reject/high risk rather than PASS; no silent success | Pass | High | Backend Engineer | Keep as false-PASS prevention evidence |

---

## D. Fallback behavior

| Case | Trigger | Expected behavior | Actual behavior | Current status | Risk level | Owner | Follow-up action |
|---|---|---|---|---|---|---|---|
| demo fallback with no selected file | real-adapter mode + no file selected | system may use demo sample, but must say so explicitly | Observed. UI clearly says `demo sample（未选择文件）` and preview text states current call uses demo sample | Pass | Low | Frontend Engineer | Keep wording in launch scope notes |
| fallback pollutes previous result | failure after previous success | old result may remain only as stale reference, never as current truth | Observed safe in analyze/verify error drills: old result is retained but clearly labeled stale/reference-only | Pass | High | Frontend Engineer + QA | Keep as regression rehearsal case |
| fallback preserves error state | error occurs after previous result exists | both error and stale warning should remain visible | Observed in analyze fail, verify fail, malformed analyze, and backend-unavailable verify drills | Pass | Medium | Frontend Engineer | No change needed before pilot |
| fallback after failure keeps UI consistent | failure path should end loading and leave consistent button state | Observed. Buttons returned to enabled state after failure; no loading hang seen | Pass | Medium | Frontend Engineer | Keep as launch evidence |

---

## E. Regression / integration observations that affect failure handling

| Observation | Evidence | Risk level | Blocking? | Owner | Follow-up action |
|---|---|---|---|---|---|
| UI request header does not update to the real adapter-generated request_id after analyze/verify | browser fetch interception captured formData request_id like `LV-SICK-...`, but visible UI still showed `REQ-2026-0424-001` mock header | High | Yes for launch auditability | Frontend Engineer | Fix request_id display / binding before pilot traffic |
| response `X-Request-Id` is not observable from frontend fetch in current browser trace | fetch wrapper captured `responseHeaderRequestId=null` for real `/analyze-document` and `/verify-attachment` calls | Medium | Potentially blocking for frontend-side evidence chain | Backend Engineer + Frontend Engineer | Verify CORS `Access-Control-Expose-Headers` and end-to-end frontend access before launch |
| direct API 422 / 400 failures currently do not return request_id in header/body | observed for invalid verify payload and empty upload | Medium | Not immediate blocker for all traffic, but weakens incident audit | Backend Engineer | Decide whether all failure responses should carry request_id |
| V1 safe-fails on partial/malformed response, but error text is technical | `Cannot read properties of undefined...` exposed to user | Medium | No, but undesirable for pilot operators | Frontend Engineer | Replace raw exception text with business-safe copy while preserving debug detail |

---

## Current conclusion

The system is already failing closed in the most important places:
- non-image upload is blocked
- corrupted image does not silently PASS
- analyze/verify failure preserves old state only as stale reference
- verify repeated click is blocked during loading

However, the pilot is not yet fully launch-safe because traceability and operator evidence still have gaps:
1. visible UI request_id does not match the real request_id used in actual calls
2. response request_id is not currently observable from the frontend trace wrapper
3. some failure responses do not carry request_id at all
4. timeout and dedicated analyze-backend-unavailable paths still need explicit rehearsal evidence
