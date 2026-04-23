# Frontend binding guide for approval verification

## Goal

Turn the current backend capability into a frontend-ready interface layer that can be:
- wired directly into a React page
- demoed with static data
- validated without waiting for more parser expansion

## 1. Column mapping

### A. Attachment column

Use these fields:

| UI block | Source field | Notes |
| --- | --- | --- |
| attachment filename | `filename` | top-level response field |
| attachment MIME type | `content_type` | decide image/pdf renderer |
| attachment status | frontend state + `verification.verify_status` | `analyzed`, `verified`, `error` are UI states; PASS/REVIEW/REJECT comes from API |
| selected doc type badge | `analysis.doc_type` | shown after analyze or verify |
| selected attachment label | `analysis.classification_evidence.attachment_label` | business-facing document label |
| quick action availability | presence of `analysis` / `verification` | enable analyze / verify buttons |

Recommended attachment row shape in frontend state:

```ts
{
  id: string;
  filename: string;
  contentType: string;
  uploadTime: string;
  sizeLabel: string;
  status: 'idle' | 'analyzing' | 'analyzed' | 'verifying' | 'verified' | 'error';
  analyzeStatus?: 'success' | 'boundary' | 'error';
  verifyStatus?: 'PASS' | 'REVIEW' | 'REJECT';
}
```

### B. OCR / analysis column

Use these fields directly from `analysis`:

| UI block | Source field | Notes |
| --- | --- | --- |
| doc type chip | `analysis.doc_type` | parser-oriented type |
| doc type confidence | `analysis.doc_type_confidence` | detector confidence |
| attachment type badge | `analysis.classification_evidence.attachment_label` | business-facing label |
| attachment type confidence | `analysis.classification_evidence.attachment_confidence` | label confidence |
| keyword evidence | `analysis.classification_evidence.matched_keywords` | show as tag list |
| field table | `analysis.extracted_fields` | main table source |
| validation accepted | `analysis.validation.accepted` | boolean summary |
| validation issues | `analysis.validation.issues` | issue list |
| review action | `analysis.review.decision.action` | often `review` today |
| OCR / pipeline warnings | `analysis.review.warnings` | show under analysis summary |
| analysis risk badge | `analysis.risk.score`, `analysis.risk.review_action` | lightweight risk block |

Recommended field table columns:
- field label
- value
- confidence
- source
- matched
- evidence text

Recommended React key:
- use `field.name`

### C. Verification column

Use these fields directly from `verification`:

| UI block | Source field | Notes |
| --- | --- | --- |
| status badge | `verification.verify_status` | PASS / REVIEW / REJECT |
| risk score bar | `verification.risk_score` | 0-100 |
| risk level badge | `verification.risk_level` | LOW / MEDIUM / HIGH |
| predicted attachment type | `verification.matched_attachment_type` | backend classification output |
| summary line | `verification.summary_message` | top summary |
| manual review hint | `verification.needs_manual_review` | disable auto-approve when true |
| warnings list | `verification.warnings` | flattened failed rule messages |
| rule list | `verification.rule_results` | main verification table/list |
| request snapshot | `verification.evidence.request` | expected types and user-entered business context |
| extracted field snapshot | `verification.evidence.fields` | keyed object, useful for compare view |
| classification snapshot | `verification.evidence.classification` | useful for detail drawer |

Recommended verification rule row shape:

```ts
{
  rule_code: string;
  passed: boolean;
  severity: 'info' | 'warning' | 'error';
  score_delta: number;
  message: string;
  evidence: Record<string, unknown>;
}
```

## 2. Response handling strategy

### Analyze flow

1. upload file to local page state
2. call `/analyze-document`
3. persist the whole payload as `analyzeResponse`
4. render attachment column + analysis column
5. do not wait for verification to render OCR details

### Verify flow

1. collect business request fields
2. call `/verify-attachment`
3. persist the whole payload as `verifyResponse`
4. use `verifyResponse.analysis` to refresh column 2 if needed
5. use `verifyResponse.verification` to render column 3

## 3. Suggested React-friendly mock data structure

Recommended folder layout:

```text
src/
  mocks/
    api/
      analyze-document.success.json
      analyze-document.boundary.partial-analysis.json
      analyze-document.error.missing-plugin.json
      verify-attachment.success.pass.json
      verify-attachment.boundary.review.json
      verify-attachment.boundary.reject.json
      verify-attachment.error.missing-expected.json
    pages/
      approval-verification-page.pass.json
      approval-verification-page.review.json
    fixtures/
      leave-request.sick.json
      leave-request.marriage.json
      attachment-list.json
    adapters/
      analyzeDocument.ts
      verifyAttachment.ts
      buildApprovalPageModel.ts
```

### What each folder is for

- `api/`: raw endpoint-level payloads, as close to backend as possible
- `pages/`: already-assembled page view models for Storybook / static page prototypes
- `fixtures/`: reusable business inputs like leave request header info
- `adapters/`: tiny mappers that normalize backend payloads into page view models

## 4. Recommended frontend page view model

Use one aggregated page model rather than binding every component straight to the raw API response.

```ts
export type ApprovalVerificationPageModel = {
  requestHeader: {
    requestId: string;
    applicantName: string;
    department: string;
    leaveType: string;
    leaveDateRange: string;
    approvalStatus: string;
  };
  attachments: Array<{
    id: string;
    filename: string;
    contentType: string;
    uploadTime: string;
    sizeLabel: string;
    status: 'idle' | 'analyzed' | 'verified' | 'error';
    docType?: string;
    attachmentLabel?: string;
    verifyStatus?: 'PASS' | 'REVIEW' | 'REJECT';
  }>;
  selectedAttachmentId: string;
  analysis: {
    docType: string;
    docTypeConfidence: number | null;
    attachmentLabel: string;
    attachmentConfidence: number | null;
    matchedKeywords: string[];
    extractedFields: Array<{
      name: string;
      value: unknown;
      confidence: number | null;
      source: string | null;
      matched: boolean;
      evidenceText: string | null;
    }>;
    validationAccepted: boolean;
    validationIssues: Array<{
      code: string;
      severity: string;
      message: string;
      field_name?: string | null;
    }>;
    reviewAction: string;
    reviewWarnings: Array<Record<string, unknown>>;
  };
  verification?: {
    verifyStatus: 'PASS' | 'REVIEW' | 'REJECT';
    riskScore: number;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
    matchedAttachmentType: string;
    summaryMessage: string;
    needsManualReview: boolean;
    warnings: string[];
    ruleResults: Array<{
      rule_code: string;
      passed: boolean;
      severity: string;
      score_delta: number;
      message: string;
      evidence: Record<string, unknown>;
    }>;
    requestEvidence: Record<string, unknown>;
    fieldEvidence: Record<string, unknown>;
  };
};
```

## 5. Minimal adapter rules

### `buildApprovalPageModel.ts`

- map `analysis.classification_evidence.attachment_label` -> `analysis.attachmentLabel`
- map `analysis.classification_evidence.attachment_confidence` -> `analysis.attachmentConfidence`
- map `analysis.review.decision.action` -> `analysis.reviewAction`
- map `verification.matched_attachment_type` -> `verification.matchedAttachmentType`
- map `verification.evidence.request` -> `verification.requestEvidence`
- map `verification.evidence.fields` -> `verification.fieldEvidence`

## 6. Recommended prototype step after docs and mocks

Because the repo has no frontend package yet, the lowest-risk next step is:
- provide a static HTML prototype or page skeleton spec first
- only then scaffold a React page when frontend hosting choices are clear

See:
- `docs/prototypes/approval-verification-page.html`
- `examples/mock-ui/approval-verification-page.pass.json`
- `examples/mock-ui/approval-verification-page.review.json`
