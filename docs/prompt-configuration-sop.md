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
| `classification` | Passed inside `inputs.prompt_texts_json`; the Dify workflow must read this key explicitly. |
| `normalization` | Passed inside `inputs.prompt_texts_json`; use it for date, name, hospital, or amount normalization guidance. |
| `risk_assessment` | Passed inside `inputs.prompt_texts_json`; use it for LLM-assisted risk scoring or review guidance. |
| `review_summary` | Passed inside `inputs.prompt_texts_json`; use it for manual-review summaries. |
| `qa_assistant` | Passed inside `inputs.prompt_texts_json`; use it for QA/chat prompt routing. |
| `callback_summary` | Passed inside `inputs.prompt_texts_json`; use it for external callback wording. |

Compatibility: existing `leave_audit_rule_config.prompt_text` still works. If no `field_extraction` prompt is configured for the recognition type, the rule `prompt_text` is used as the fallback Dify extraction prompt.

## 2. Configure by UI

1. Open the approval verification frontend.
2. Go to the `提示词配置` tab.
3. Choose an existing config or fill a new `识别类型` and `提示词类型`.
4. Keep `启用` on for active prompts.
5. Save the config.
6. Run the target task with `Dify解析`.
7. Open the task drawer and check `提示词追踪`.

Important behavior:

- A concrete recognition type, such as `diagnosis_proof`, overrides `*` for the same prompt type.
- Disabled prompts are not passed to Dify.
- `field_extraction` is the prompt type that directly changes `inputs.custom_prompt`.
- `verification` directly changes `inputs.verification_prompt`.
- Other prompt types are available in `inputs.prompt_texts_json`. They only affect the Dify app if the workflow parses this JSON and reads the matching key.

## 3. Configure by API

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

## 4. Configure by SQL

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

## 5. Dify Workflow Inputs

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

If the workflow needs non-extraction prompts, parse `prompt_texts_json`. Example workflow logic:

```text
Read prompt_texts_json as JSON.
Use prompt_texts.classification only when classifying the document.
Use prompt_texts.normalization only when normalizing extracted field values.
Use prompt_texts.risk_assessment only when preparing review or risk guidance.
```

## 6. Prompt Writing Rules

- Use internal field names, not display names. Example: write `patient_name`, not `患者姓名`.
- State negative constraints explicitly. Example: "不要把医生姓名当成患者姓名。"
- Keep extraction prompts about extraction only. Put approval policy in `verification`.
- Do not ask the model to output markdown or explanations.
- Require null for unknown values; do not let the model invent placeholders.
- Keep dates in `YYYY-MM-DD` when possible.
- Keep one recognition type focused on one document category.
- Do not put rule logic only in `verification` and expect deterministic approval behavior. Put deterministic checks in rule JSON.
- For new prompt types, first update the Dify workflow to read `prompt_texts_json`, then add the DB config.

## 7. Common Recognition Types

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

## 8. Troubleshooting

If a custom prompt does not seem effective:

1. Confirm the task was run with `field_parser_backend=dify`; local plugin parsing does not use LLM prompts.
2. Check `/leave-audit/config` and confirm the prompt is enabled.
3. Check `analysis_json.raw_artifacts.prompt_context` in the task result.
4. For Dify workflow apps, confirm the workflow declares and uses `custom_prompt`.
5. If the prompt type is not `field_extraction` or `verification`, confirm the workflow reads `prompt_texts_json` and the exact prompt key.
6. Confirm the prompt uses plugin field names from `target_fields_json`.
7. If using old rule config only, confirm `leave_type` matches the task, such as `SICK` or `MARRIAGE`.
