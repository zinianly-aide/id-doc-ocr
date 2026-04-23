# Approval verification UI structure design

## Goal

Provide a minimal approval-verification page structure for leave approval scenarios that consumes:

- `POST /analyze-document`
- `POST /verify-attachment`

The page is optimized for the workflow:

1. upload attachment
2. inspect OCR / extracted fields
3. inspect verification result
4. make approval decision

## Page layout

Use a three-column working area under the leave-request header.

### Top header area

Show fixed request context above the columns:

- applicant name
- department
- leave type
- leave date range
- request id
- approval status
- back button / breadcrumb

Recommended tabs:

- approval info
- attachment verification
- approval flow
- operation history

Default active tab for this project: `attachment verification`.

## Main three-column structure

### Column 1 — Attachment column

Purpose:
- attachment selection
- file preview entry
- upload / replace / re-run analysis

Recommended blocks:

1. attachment list
   - filename
   - upload time
   - file size
   - current processing state
   - selected item highlight

2. upload area
   - drag-and-drop
   - supported formats
   - file size limit

3. quick actions
   - analyze document
   - verify attachment
   - replace file

Recommended API bindings:
- upload only stores file locally/in-temp state
- `analyze` calls `/analyze-document`
- `verify` calls `/verify-attachment`

### Column 2 — OCR / analysis column

Purpose:
- show document preview and machine-readable extraction result

Recommended vertical split:

1. preview card
   - image/pdf preview
   - zoom / rotate controls
   - page navigation if multi-page is added later

2. analysis card
   - classification label
   - classification confidence
   - OCR confidence if available
   - extracted field list
   - raw OCR snippet
   - evidence regions later if bbox overlay is added

Map directly from `analysis`:

- `analysis.doc_type`
- `analysis.doc_type_confidence`
- `analysis.classification_evidence.attachment_label`
- `analysis.classification_evidence.attachment_confidence`
- `analysis.classification_evidence.matched_keywords`
- `analysis.extracted_fields`
- `analysis.validation`
- `analysis.review`

Suggested field table columns:

- field name
- value
- confidence
- source
- matched/evidence status

### Column 3 — Verification column

Purpose:
- show approval-facing verification outcome instead of raw OCR detail

Recommended blocks:

1. verification summary
   - PASS / REVIEW / REJECT
   - risk level
   - risk score
   - matched attachment type
   - summary message

2. rule results list
   - rule code
   - passed/failed state
   - severity
   - score delta
   - short explanation

3. request-vs-document evidence
   - applicant name
   - related person name / relation if provided
   - leave dates
   - resolved expected attachment types
   - key extracted fields used by rules

4. recommendation area
   - auto-approve
   - manual review required
   - reject recommendation

Map directly from `verification`:

- `verification.verify_status`
- `verification.risk_score`
- `verification.risk_level`
- `verification.matched_attachment_type`
- `verification.rule_results`
- `verification.warnings`
- `verification.needs_manual_review`
- `verification.summary_message`
- `verification.evidence`

## Minimal interaction flow

### First load

If attachment already exists:
- load request summary
- show attachment list
- fetch latest stored analysis/verification if available
- default selected tab: attachment verification

### User-driven flow

1. user selects or uploads attachment
2. frontend calls `/analyze-document`
3. render preview + OCR + extracted fields
4. user confirms or edits request-side parameters
5. frontend calls `/verify-attachment`
6. render PASS / REVIEW / REJECT and rule details
7. approver decides approve / reject / send for manual review

## API-to-UI mapping summary

### Analyze response

Use for column 2 mostly:

- `result` — full pipeline payload for debugging
- `analysis` — normalized UI-facing analysis object

### Verify response

Use for columns 2 and 3:

- `analysis` — same normalized analysis object
- `verification` — approval-facing decision object
- `result` — full low-level payload for debug drawer or developer mode

## Recommended UX states

### Processing
- analyzing...
- verifying...
- disable duplicate submits

### Success
- green summary for PASS
- amber summary for REVIEW
- red summary for REJECT

### Error
- backend validation errors shown inline
- unknown plugin / empty file / invalid request surfaced at top of column

## Minimal data contracts needed by frontend

### Analyze request

- `plugin_name`
- `file`
- optional OCR backend selection
- optional extracted field overrides for parser assistance

### Verify request

- all analyze inputs
- one of:
  - `expected_attachment_type`
  - `expected_attachment_types`
  - `leave_type`
- optional:
  - `applicant_name`
  - `related_person_name`
  - `related_person_relation`
  - `leave_start_date`
  - `leave_end_date`

## Future UI extensions

Not required for MVP, but compatible with current backend direction:

- bounding-box overlay on preview
- confidence heatmap for fields
- similar-case recommendations panel
- verification history timeline
- manual correction and re-verify loop
- side-by-side applicant form vs extracted attachment fields
