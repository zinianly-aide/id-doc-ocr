# Approval Verification Stability Regression Report

## Purpose

This report summarizes the current regression and stability validation round from the perspective of a pilot-stability owner.

Focus of this round:
1. false-PASS prevention
2. stale-state / fallback safety
3. request traceability
4. REVIEW path operability
5. launch-evidence collection

---

## 1. Executed checks

### Code / build regression
- backend targeted regression: `25 passed`
- frontend production build: passed

### Browser / UI regression
Executed on local V1 page in real-adapter mode:
- SICK baseline page state
- MARRIAGE REVIEW page state
- analyze fail simulation
- verify fail simulation
- non-image upload
- corrupted image upload
- stale verify result after failure
- malformed analyze response
- partial verify response
- repeated verify click with loading lock
- frontend request_id interception drill

### Direct API regression
Executed against local backend validation instance:
- verify invalid payload
- analyze non-image
- analyze empty file
- analyze corrupted image
- request_id log trace sample

---

## 2. Regression result table

| Case | Channel | Result | Reproducible | Severity | Blocking | Notes |
|---|---|---|---|---|---|---|
| SICK page baseline visible | UI | Pass | Yes | Low | No | V1 baseline loads and shows PASS state |
| MARRIAGE REVIEW baseline visible | UI | Pass | Yes | Medium | No | REVIEW state and MARRIAGE request context visible |
| analyze fail | UI | Pass | Yes | Medium | No | fail-closed + stale analysis warning |
| verify fail | UI | Pass | Yes | High | No | fail-closed + stale verify warning |
| non-image upload | UI | Pass | Yes | Medium | No | blocked client-side with explicit message |
| corrupted image | UI/API | Pass | Yes | High | No | did not silently PASS |
| empty file | API | Partial | Yes | Medium | No | backend 400 clear; UI drill not yet done |
| verify invalid payload | API | Partial | Yes | Medium | No | backend 422 clear; no request_id on error |
| backend unavailable on verify path | UI | Pass | Yes | High | No | stale verify result clearly marked reference-only |
| malformed analyze response | UI | Pass | Yes | Medium | No | parse error surfaced, stale analysis retained |
| partial verify response | UI | Partial | Yes | High | Yes | fail-closed, but user sees raw technical error |
| repeated verify click | UI | Pass | Yes | Low | No | verify button disabled during loading |
| request_id frontend/back mismatch | UI/adapter | Fail | Yes | High | Yes | UI still shows mock request id instead of real adapter request id |
| response request_id visible to frontend JS | UI/backend | Fail | Yes | Medium | Yes | browser fetch wrapper could not read `X-Request-Id` |
| backend log trace | API/backend | Pass | Yes | Medium | No | local validation backend log linked request_id across stages |

---

## 3. Key findings

### 3.1 Good news
- the system is generally failing closed rather than silently passing bad states
- stale-state wording is present and understandable
- duplicate verify click is already guarded by loading disable
- direct request_id plumbing exists in both adapter and backend
- marriage gating baseline is already in place and remains intact

### 3.2 Main launch risks
- visible UI requestId is currently misleading for live requests
- response request_id is not observable from frontend JS in current setup
- override auditing is not product-enforced
- some failure branches still surface technical exception text directly to the operator

### 3.3 False-PASS perspective
The most important validation outcome from this round is positive:
- non-image does not proceed as if valid
- corrupted image does not silently PASS
- verify failure does not silently preserve a “current PASS” state without warning

That said, a traceability gap can still make a pilot operationally unsafe even when decision logic fails closed.

---

## 4. Launch recommendation from stability owner

Recommendation:
- continue toward launch freeze
- do not start pilot traffic yet

Required closures before pilot traffic:
1. align UI-visible requestId with runtime request_id
2. confirm frontend can access echoed request_id, or define another explicit operator-facing trace source
3. freeze external review / override ledger discipline
4. close the remaining unexecuted failure drills

---

## 5. Most important next actions

1. Fix or explicitly resolve request_id trace visibility in the UI path.
2. Run the remaining launch drills: analyze-timeout, analyze-backend-unavailable, empty-file UI path.
3. Freeze operator ledger ownership so REVIEW / override becomes auditable in practice.
