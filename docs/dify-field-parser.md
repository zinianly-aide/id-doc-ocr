# Dify Field Parser Backend

This is an experimental parser path for validating Dify as a schema-aware field extractor.

The default parser remains the local plugin parser. Dify is only used when `field_parser_backend=dify`
is passed in the request or `ID_DOC_OCR_DEFAULT_FIELD_PARSER_BACKEND=dify` is set.

## Environment

Global API key:

```bash
export ID_DOC_OCR_DIFY_API_KEY="app-xxx"
export ID_DOC_OCR_DIFY_BASE_URL="https://api.dify.ai/v1"
```

Schema-specific API key:

```bash
export ID_DOC_OCR_DIFY_DIAGNOSIS_PROOF_API_KEY="app-xxx"
```

Optional schema-specific target fields:

```bash
export ID_DOC_OCR_DIFY_DIAGNOSIS_PROOF_TARGET_FIELDS="hospital_name,diagnosis,issue_date,patient_name,rest_start_date,rest_end_date"
```

Optional app type:

```bash
export ID_DOC_OCR_DIFY_APP_TYPE="workflow"
```

Supported app types:

- `workflow`: `POST /workflows/run`
- `chat`: `POST /chat-messages`
- `completion`: `POST /completion-messages`

## Request

```bash
curl -sS http://127.0.0.1:8000/infer \
  -F plugin_name=diagnosis_proof \
  -F ocr_backend=paddleocr \
  -F vlm_backend=mock \
  -F detector_backend=pil \
  -F rectify_backend=pil \
  -F field_parser_backend=dify \
  -F file=@examples/assets/sick_leave_normal_generated/diagnosis_generated_001.png
```

## Dify Input Contract

The parser sends these workflow inputs:

```json
{
  "schema_name": "diagnosis_proof",
  "plugin_name": "diagnosis_proof",
  "ocr_text": "...",
  "ocr_lines": [],
  "ocr_lines_json": "[]",
  "target_fields": ["hospital_name", "diagnosis", "issue_date"],
  "target_fields_json": "[\"hospital_name\", \"diagnosis\", \"issue_date\"]"
}
```

## Dify Output Contract

Return either:

```json
{
  "fields": {
    "hospital_name": "测试医院",
    "diagnosis": ["上呼吸道感染"],
    "issue_date": "2026-05-20"
  }
}
```

Or put the same `fields` object inside workflow `data.outputs.fields`.

The field names must be internal canonical names used by the plugin validators.
