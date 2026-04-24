# Approval verification React page skeleton

## Status

A mock-first React page skeleton is now available at:

- `ui/approval-verification/`

It is intentionally scoped to:
- render UI from `examples/mock-ui/approval-verification-page.pass.json`
- render UI from `examples/mock-ui/approval-verification-page.review.json`
- validate component boundaries
- validate field binding
- validate page state flow

It does not:
- call real upload APIs
- bind debug-only backend internals into the main UI
- expand parser scope or document coverage

It now additionally supports a minimal `real adapter mode`:
- page shell still comes from mock page models
- analyze / verify buttons can call real `/analyze-document` and `/verify-attachment`
- requests use an internal demo sample image instead of user upload

## 1. Page component structure

Entry files:
- `ui/approval-verification/src/App.tsx`
- `ui/approval-verification/src/components/ApprovalVerificationPage.tsx`

Component tree:

- `App`
  - scenario switcher (`pass` / `review`)
  - `ApprovalVerificationPage`
    - `AttachmentList`
    - `DocumentPreview`
    - `AnalysisPanel`
    - `VerificationPanel`
      - `RuleResultList`
    - `RiskBadge`

### Component responsibilities

#### `ApprovalVerificationPage`
Owns the page-level interaction state and orchestrates three-column rendering.

Responsibilities:
- hold page state
- trigger mock analyze / verify actions
- bind selected attachment to center / right columns
- expose current error and async status

#### `AttachmentList`
Left column.

Responsibilities:
- render available attachments
- show selected row
- show simple attachment metadata
- surface analyze / verify state summary

Bound fields:
- `attachments[]`
- `selectedAttachmentId`
- `attachment.filename`
- `attachment.contentType`
- `attachment.sizeLabel`
- `attachment.docType`
- `attachment.attachmentLabel`
- `attachment.verifyStatus`

#### `DocumentPreview`
Top area of middle column.

Responsibilities:
- render request header summary
- render current attachment preview placeholder
- reserve the future image/pdf preview slot

Bound fields:
- `requestHeader`
- selected attachment filename / content type
- `analysis.doc_type`
- `analysis.classification_evidence.attachment_label`
- `analysis.extracted_fields.length`

#### `AnalysisPanel`
Main middle column detail area.

Responsibilities:
- render document analysis summary
- render extracted field table
- render validation issues
- render review warnings

Bound fields:
- `analysis.doc_type`
- `analysis.doc_type_confidence`
- `analysis.classification_evidence.attachment_label`
- `analysis.classification_evidence.attachment_confidence`
- `analysis.classification_evidence.matched_keywords`
- `analysis.extracted_fields`
- `analysis.validation`
- `analysis.review`
- `analysis.risk.review_action`

#### `VerificationPanel`
Right column.

Responsibilities:
- render verification summary
- render summary message
- render risk status
- render request evidence
- render warnings
- delegate rule list rendering

Bound fields:
- `verification.verify_status`
- `verification.risk_score`
- `verification.risk_level`
- `verification.matched_attachment_type`
- `verification.summary_message`
- `verification.needs_manual_review`
- `verification.rule_results`
- `verification.evidence.request`
- `verification.warnings`

#### `RuleResultList`
Responsibilities:
- render `rule_results[]`
- show rule code, pass/fail, severity, score_delta, message

#### `RiskBadge`
Responsibilities:
- normalize PASS / REVIEW / REJECT / LOW / MEDIUM / HIGH / INFO visual styles
- keep badge styling consistent across panels

## 2. Raw response → ViewModel mapping

The page now explicitly separates adapter input from component input.

### Raw response types
- `RawAnalyzeResponse`
- `RawVerifyResponse`
- `RawApprovalVerificationPageModel`

These represent backend-oriented or mock-file-oriented shapes.

### UI-facing ViewModel types
- `ApprovalVerificationViewModel`
- `AttachmentViewModel`
- `AnalysisViewModel`
- `VerificationViewModel`

These represent the three-column page contract.

### Mapping function
`buildApprovalPageModel()` now owns the conversion from:
- mock page model shell
- raw analyze response
- raw verify response

to:
- request header for the page
- attachment list for the left column
- analysis panel model for the middle column
- verification panel model for the right column

### Request builders
The real adapter no longer assembles FormData inside page components.

Instead it uses:
- `buildAnalyzeDemoFormData()`
- `buildVerifyDemoFormData()`

This means that when real upload is added later, the first replacement point should be the request builder layer, not the page components.

## 3. Data flow

### Initial load

1. `App` keeps a top-level `scenario` state: `pass` or `review`
2. `App` calls `getApprovalVerificationMock(scenario)`
3. the adapter loads the matching mock page model from `examples/mock-ui/*.json`
4. `App` passes `pageModel` into `ApprovalVerificationPage`
5. `ApprovalVerificationPage` hydrates its internal state from `pageModel`

### Analyze flow

1. user clicks `Run mock analyze`
2. `ApprovalVerificationPage` sets `analyzeStatus = loading`
3. page calls `analyzeDocument(scenario)`
4. adapter returns `analyzeResponse`
5. page updates:
   - `currentAnalysis`
   - `analyzeStatus = success`
   - `error = null`

### Verify flow

1. user clicks `Run mock verify`
2. `ApprovalVerificationPage` sets `verifyStatus = loading`
3. page calls `verifyAttachment(scenario)`
4. adapter returns `verifyResponse`
5. page updates:
   - `currentAnalysis`
   - `currentVerification`
   - `verifyStatus = success`
   - `error = null`

### Attachment selection flow

1. user clicks an attachment in `AttachmentList`
2. page updates `selectedAttachmentId`
3. `DocumentPreview` uses the selected attachment metadata
4. current MVP mock only has one attachment per page model, but the state shape already supports multiple attachments

## 3. Mock adapter design

File:
- `ui/approval-verification/src/adapters/mockApprovalVerification.ts`

Exported interface:
- `getApprovalVerificationMock(scenario?: "pass" | "review")`
- `analyzeDocument(scenario?: "pass" | "review")`
- `verifyAttachment(scenario?: "pass" | "review")`

### What the adapter does

- imports the existing repo mock files directly:
  - `examples/mock-ui/approval-verification-page.pass.json`
  - `examples/mock-ui/approval-verification-page.review.json`
- clones the payload before returning it
- simulates async behavior with a small delay
- returns typed data objects for React consumption

### Why this adapter shape is useful

It matches the future real integration path:
- page code already depends on async functions
- later only the adapter implementation changes
- the page component API does not need to change when moving from mock to real backend

## 4. Page state design

Inside `ApprovalVerificationPage` the page keeps:

- `selectedAttachmentId`
- `analyzeStatus`
- `verifyStatus`
- `currentAnalysis`
- `currentVerification`
- `error`

### State meaning

#### `selectedAttachmentId`
Controls which attachment row is active and which attachment metadata is shown in `DocumentPreview`.

#### `analyzeStatus`
Async state for the mock analyze action.

Current values:
- `idle`
- `loading`
- `success`
- `error`

#### `verifyStatus`
Async state for the mock verify action.

Current values:
- `idle`
- `loading`
- `success`
- `error`

#### `currentAnalysis`
The current normalized analysis payload used by the middle column.

#### `currentVerification`
The current normalized verification payload used by the right column.

#### `error`
Stores the latest page-level action failure.

## 5. Fields intentionally prioritized in the UI

The page skeleton gives priority to explainable fields:
- `doc_type`
- `extracted_fields`
- `rule_results`
- `summary_message`
- `risk_level`

It intentionally does not bind these as primary UI fields:
- `result.detector`
- `result.rectify`
- `result.ocr`
- `result.vlm`
- `analysis.raw_artifacts`

## 6. Run instructions

```bash
cd ui/approval-verification
npm install
npm run dev
```

Build verification used in this repo:

```bash
cd ui/approval-verification
npm run build
```

## 7. Next-step real API integration suggestion

Do this in order, without changing the page component boundaries first.

### Step 1
Keep the page and components unchanged. Only replace the mock adapter implementation.

### Step 2
Change:
- `getApprovalVerificationMock()` into a thin loader for a seeded page shell or remove it entirely
- `analyzeDocument()` to call `POST /analyze-document`
- `verifyAttachment()` to call `POST /verify-attachment`

### Step 3
Add a small request-builder layer for multipart form construction.

Suggested adapter split later:
- `buildAnalyzeFormData()`
- `buildVerifyFormData()`
- `analyzeDocument()`
- `verifyAttachment()`
- `buildApprovalPageModel()`

### Step 4
When real API wiring starts, keep binding limited to these stable fields:
- `analysis.doc_type`
- `analysis.doc_type_confidence`
- `analysis.classification_evidence.attachment_label`
- `analysis.extracted_fields`
- `analysis.validation`
- `analysis.review`
- `verification.verify_status`
- `verification.risk_score`
- `verification.risk_level`
- `verification.rule_results`
- `verification.summary_message`
- `verification.evidence.request`

### Step 5
Only after the real adapter is stable should the preview block be replaced with:
- actual uploaded image preview
- pdf preview
- upload queue state

Do not couple that work to the current React skeleton step.
