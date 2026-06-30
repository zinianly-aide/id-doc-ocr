# Leave Audit Rule Configuration SOP

This SOP explains how to configure leave-audit rule JSON in the database.

## 1. Configure Rules by API

Read current config:

```bash
curl -sS http://127.0.0.1:8000/leave-audit/config
```

Update rules for a leave type:

```bash
curl -sS -X PUT http://127.0.0.1:8000/leave-audit/config/rules \
  -H 'Content-Type: application/json' \
  -d '{
    "configs": [
      {
        "leave_type": "SICK",
        "prompt_text": "病假材料需核对患者姓名、诊断和休假日期。",
        "enabled": true,
        "rules": [
          {
            "type": "required_field",
            "rule_code": "sick_required_fields",
            "fields": ["patient_name", "rest_start_date", "rest_end_date"],
            "on_fail": "REJECT",
            "message_zh": "病假材料必须包含患者姓名和休假起止日期"
          },
          {
            "type": "date_coverage",
            "rule_code": "sick_rest_period_covers_leave",
            "on_fail": "REVIEW",
            "message_zh": "材料休假日期应覆盖请假日期"
          }
        ]
      }
    ]
  }'
```

Run a task:

```bash
curl -sS -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-xxx/run
```

Check `verification_json.rule_results` in:

```bash
curl -sS http://127.0.0.1:8000/leave-audit/tasks/LV-xxx
```

## 2. Supported Rule Types

### `date_window`

Checks that leave dates fall within a window after a document date.

```json
{
  "type": "date_window",
  "rule_code": "marriage_registration_date_window",
  "date_field": "registration_date",
  "max_years": 1,
  "on_fail": "REJECT"
}
```

### `required_name`

Checks that the applicant appears in configured name candidates or extracted values.

```json
{
  "type": "required_name",
  "rule_code": "applicant_must_appear",
  "candidates": ["patient_name", "holder_name"],
  "on_fail": "REJECT"
}
```

### `required_field`

Checks required extracted fields.

```json
{
  "type": "required_field",
  "rule_code": "sick_required_fields",
  "fields": ["patient_name", "rest_start_date", "rest_end_date"],
  "mode": "all",
  "on_fail": "REJECT"
}
```

Use `"mode": "any"` when at least one field is enough.

### `date_coverage`

Checks that a document date range covers the request leave date range.

```json
{
  "type": "date_coverage",
  "rule_code": "rest_period_covers_leave",
  "document_start_field": "rest_start_date",
  "document_end_field": "rest_end_date",
  "request_start_field": "leave_start_date",
  "request_end_field": "leave_end_date",
  "on_fail": "REVIEW"
}
```

### `field_equals`

Checks exact equality against a literal expected value or a request field.

```json
{
  "type": "field_equals",
  "rule_code": "patient_name_equals_applicant",
  "field": "patient_name",
  "request_field": "applicant_name",
  "on_fail": "REJECT"
}
```

Literal value:

```json
{
  "type": "field_equals",
  "rule_code": "certificate_title_is_valid",
  "field": "certificate_title",
  "expected": "中华人民共和国结婚证",
  "on_fail": "REVIEW"
}
```

### `field_contains`

Checks that a field contains a keyword. Lists are supported.

```json
{
  "type": "field_contains",
  "rule_code": "diagnosis_has_illness_signal",
  "field": "diagnosis",
  "any_of": ["感染", "发热", "骨折"],
  "on_fail": "REVIEW"
}
```

## 3. Failure Policy

- `on_fail=REJECT`: failed rule becomes an error and blocks auto-pass.
- Any other value: failed rule becomes a warning and routes to manual review.
- `score_delta` can override default risk contribution.
- `message_zh` controls the user-facing display message.

## 4. Field Names

Rules must use internal extracted field names, for example:

- `patient_name`
- `rest_start_date`
- `rest_end_date`
- `issue_date`
- `diagnosis`
- `holder_name`
- `registration_date`
- `person_a_name`
- `person_b_name`

Use `/leave-audit/tasks/{request_id}` and inspect `analysis_json.extracted_fields` to confirm exact field names.
