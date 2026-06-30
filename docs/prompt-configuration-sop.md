# OCR Prompt Configuration SOP

This SOP explains how to configure prompt text from the leave-audit database and verify that the prompt is actually used.

## 1. Concepts

Prompt configs are stored by recognition type and prompt type.

- `recognition_type`: OCR plugin name, such as `diagnosis_proof`, `marriage_certificate`, `birth_certificate`, or `*` for global default.
- `prompt_type`: the prompt purpose.
- `prompt_text`: business instructions.
- `enabled`: whether this prompt is active.

The current effective prompt types are:

| prompt_type | Current effect |
| --- | --- |
| `field_extraction` | Passed to Dify field parsing. Workflow apps receive it as `inputs.custom_prompt`; chat/completion apps include it in the query. |
| `verification` | Stored with the run as verification guidance and passed in `inputs.verification_prompt`; rules are still controlled by rules JSON. |
| `review_summary` | Stored for manual review or future LLM summary use. |
| `qa_assistant` | Stored for future QA/chat prompt routing. |

Compatibility: existing `leave_audit_rule_config.prompt_text` still works. If no `field_extraction` prompt is configured for the recognition type, the rule `prompt_text` is used as the fallback Dify extraction prompt.

## 2. Configure by API

1. Check existing config:

```bash
curl -sS http://127.0.0.1:8000/leave-audit/config
```

2. Add or update a diagnosis-proof extraction prompt:

```bash
curl -sS -X PUT http://127.0.0.1:8000/leave-audit/config/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "configs": [
      {
        "recognition_type": "diagnosis_proof",
        "prompt_type": "field_extraction",
        "prompt_text": "只抽取病假证明相关字段。必须优先识别 patient_name、issue_date、rest_start_date、rest_end_date、diagnosis。不要把医生姓名当成患者姓名。",
        "enabled": true
      }
    ]
  }'
```

3. Add verification guidance:

```bash
curl -sS -X PUT http://127.0.0.1:8000/leave-audit/config/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "configs": [
      {
        "recognition_type": "diagnosis_proof",
        "prompt_type": "verification",
        "prompt_text": "病假证明必须包含患者姓名和休假起止日期；休假日期应覆盖请假日期；材料类型必须是医疗证明。",
        "enabled": true
      }
    ]
  }'
```

4. Run a task with Dify parsing:

```bash
curl -sS -X POST 'http://127.0.0.1:8000/leave-audit/tasks/LV-xxx/run?field_parser_backend=dify'
```

5. Verify the prompt was loaded:

```bash
curl -sS http://127.0.0.1:8000/leave-audit/tasks/LV-xxx
```

Check:

- `result.analysis_json.raw_artifacts.prompt_context.prompt_texts.field_extraction`
- `result.analysis_json.raw_artifacts.prompt_context.custom_prompt`
- `result.analysis_json.raw_artifacts.prompt_context.verification_prompt`

## 3. Configure by SQL

Use SQL only when you need direct DB maintenance.

```sql
INSERT INTO leave_audit_prompt_config
  (recognition_type, prompt_type, prompt_text, enabled, updated_at)
VALUES
  ('diagnosis_proof', 'field_extraction', '只抽取病假证明字段...', 1, datetime('now'))
ON CONFLICT(recognition_type, prompt_type) DO UPDATE SET
  prompt_text = excluded.prompt_text,
  enabled = excluded.enabled,
  updated_at = excluded.updated_at;
```

Disable a prompt:

```sql
UPDATE leave_audit_prompt_config
SET enabled = 0, updated_at = datetime('now')
WHERE recognition_type = 'diagnosis_proof'
  AND prompt_type = 'field_extraction';
```

## 4. Dify Workflow Inputs

For workflow apps, configure Dify input variables with these names:

- `schema_name`
- `plugin_name`
- `recognition_type`
- `leave_type`
- `ocr_text`
- `ocr_lines_json`
- `target_fields_json`
- `custom_prompt`
- `verification_prompt`
- `prompt_texts_json`

Recommended workflow instruction:

```text
You are extracting fields from OCR text.
Follow custom_prompt first.
Return only JSON:
{"fields": {"field_name": "value"}}
Only use field names listed in target_fields_json.
If unknown, return null.
```

## 5. Prompt Writing Rules

- Use internal field names, not display names. Example: write `patient_name`, not `患者姓名`.
- State negative constraints explicitly. Example: "不要把医生姓名当成患者姓名。"
- Keep extraction prompts about extraction only. Put approval policy in `verification`.
- Do not ask the model to output markdown or explanations.
- Require null for unknown values; do not let the model invent placeholders.
- Keep dates in `YYYY-MM-DD` when possible.
- Keep one recognition type focused on one document category.

## 6. Common Recognition Types

Use these `recognition_type` values for current plugins:

- `diagnosis_proof`
- `medical_record`
- `marriage_certificate`
- `birth_certificate`
- `only_child_certificate`
- `custody_relationship_certificate`
- `hukou_booklet`
- `train_ticket`
- `boarding_pass`
- `passport`
- `china_id`

Use `*` only for global defaults. A concrete recognition type overrides `*` for the same prompt type.

## 7. Troubleshooting

If a custom prompt does not seem effective:

1. Confirm the task was run with `field_parser_backend=dify`; local plugin parsing does not use LLM prompts.
2. Check `/leave-audit/config` and confirm the prompt is enabled.
3. Check `analysis_json.raw_artifacts.prompt_context` in the task result.
4. For Dify workflow apps, confirm the workflow declares and uses `custom_prompt`.
5. Confirm the prompt uses plugin field names from `target_fields_json`.
6. If using old rule config only, confirm `leave_type` matches the task, such as `SICK` or `MARRIAGE`.
