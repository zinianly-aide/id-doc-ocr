# Minimal rule matrix and runnable demo flow

## Scope

This document intentionally keeps the matrix minimal.

Only cover:
- `SICK`
- `MARRIAGE`

Do not expand to more document types before this workflow is stable.

## 1. Minimal rule matrix

### Leave type: SICK

Accepted attachment types:
- `MEDICAL_CERTIFICATE`

Primary extracted fields:
- `patient_name`
- `rest_start_date`
- `rest_end_date`
- `issue_date`
- optional medical context fields such as `hospital_name`, `diagnosis`, `physician_name`

Request-side fields:
- `applicant_name`
- `leave_start_date`
- `leave_end_date`
- `leave_type=SICK`

Minimal rules:

1. attachment_type_match
   - predicted attachment label must be `MEDICAL_CERTIFICATE`

2. applicant_name_match
   - `patient_name` should match `applicant_name`

3. leave_date_match
   - document rest dates should align with request leave dates

Relation rule:
- no related-person requirement for `SICK`

Field mapping:
- business subject = `applicant_name`
- document subject = `patient_name`
- effective date start = `rest_start_date`
- effective date end = `rest_end_date`

### Leave type: MARRIAGE

Accepted attachment types:
- `MARRIAGE_CERTIFICATE`

Primary extracted fields:
- `holder_name`
- `person_a_name`
- `person_b_name`
- `registration_date`
- optional `registration_authority`, `certificate_number`

Request-side fields:
- `applicant_name`
- `related_person_name`
- `related_person_relation=spouse`
- `leave_type=MARRIAGE`
- optional leave dates

Minimal rules:

1. attachment_type_match
   - predicted attachment label must be `MARRIAGE_CERTIFICATE`

2. applicant_name_match
   - applicant should match certificate holder or one spouse field

3. related_person_match
   - related person should match the spouse counterpart in the certificate

4. leave_date_match
   - optional in MVP; can align leave dates with registration date when business requires it

Relation rule:
- `related_person_relation` should be `spouse`

Field mapping:
- business subject = `applicant_name`
- document subject = `holder_name` or `person_a_name`
- business related person = `related_person_name`
- document related person = `person_b_name`
- reference date = `registration_date`

## 2. Current backend support summary

Already supported in backend:
- unified `analysis` payload
- `verification.verify_status`
- `expected_attachment_type`
- `expected_attachment_types`
- `leave_type`
- `related_person_name`
- `related_person_relation`
- resolved expected attachment types in `verification.evidence.request`

Current leave-type matrix in code:
- `SICK -> [MEDICAL_CERTIFICATE]`
- `MARRIAGE -> [MARRIAGE_CERTIFICATE]`
- `MATERNITY -> [BIRTH_CERTIFICATE, MEDICAL_CERTIFICATE]`

For the MVP described here, frontend should actively use only `SICK` and `MARRIAGE`.

## 3. Minimal runnable demo flow

### Demo goal

Show the full chain:

upload -> analyze -> verify -> UI render

### Step A — upload attachment

Frontend collects:
- leave request summary
- attachment file
- plugin name for the MVP route

Example sick-leave attachment:
- `plugin_name=diagnosis_proof`
- file = diagnosis proof image

### Step B — analyze document

Call:

```bash
curl -X POST http://127.0.0.1:8000/analyze-document \
  -F plugin_name=diagnosis_proof \
  -F ocr_backend=mock \
  -F vlm_backend=mock \
  -F patient_name=张三 \
  -F rest_start_date=2026-04-01 \
  -F rest_end_date=2026-04-03 \
  -F issue_date=2026-04-01 \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

Frontend renders:
- preview card
- extracted field list
- attachment label and confidence
- raw OCR snippet

### Step C — verify attachment

Sick leave example:

```bash
curl -X POST http://127.0.0.1:8000/verify-attachment \
  -F plugin_name=diagnosis_proof \
  -F ocr_backend=mock \
  -F vlm_backend=mock \
  -F leave_type=SICK \
  -F applicant_name=张三 \
  -F leave_start_date=2026-04-01 \
  -F leave_end_date=2026-04-03 \
  -F patient_name=张三 \
  -F rest_start_date=2026-04-01 \
  -F rest_end_date=2026-04-03 \
  -F issue_date=2026-04-01 \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

Marriage leave example:

```bash
curl -X POST http://127.0.0.1:8000/verify-attachment \
  -F plugin_name=marriage_certificate \
  -F ocr_backend=mock \
  -F vlm_backend=mock \
  -F leave_type=MARRIAGE \
  -F applicant_name=张三 \
  -F related_person_name=李四 \
  -F related_person_relation=spouse \
  -F holder_name=张三 \
  -F person_a_name=张三 \
  -F person_b_name=李四 \
  -F registration_date=2024-05-20 \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

### Step D — UI render

Render three columns:

1. attachment column
- uploaded file
- status
- actions

2. OCR / analysis column
- preview
- extracted fields
- attachment label

3. verification column
- PASS / REVIEW / REJECT
- risk score
- rule list
- recommendation

## 4. MVP success criteria

The MVP is considered runnable when:

1. `/analyze-document` returns analysis payload for uploaded files
2. `/verify-attachment` returns verification payload for `SICK` and `MARRIAGE`
3. UI can render three columns from these two APIs
4. approver can understand why the result is PASS / REVIEW / REJECT without opening raw backend logs

## 5. What not to do before MVP is stable

Do not prioritize these yet:
- adding more document types
- complex similarity retrieval
- large rule catalogs
- visual bbox overlay polish
- multi-page workflow expansion

Keep the system narrow and stable first.
