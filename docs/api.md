# API quickstart

The repo now exposes a minimal HTTP service for local development and container deployment.

For deployment and operational guidance beyond the endpoint examples here, see [deployment.md](deployment.md).

## Endpoints

### `GET /health`

Returns service liveness plus a lightweight runtime snapshot:

- service name / version
- registered plugin names
- backbone availability summary
- detector / rectify availability summary
- runtime metadata
- default failure directory
- default detector / rectify backends

### `GET /capabilities`

Returns the fuller machine-readable inventory used for readiness checks and UI bootstrapping:

- plugin metadata (`name`, `schema`, `tags`, supported backbones)
- plugin maturity data (`maturity`, `regression`, `trial_profile`)
- OCR / VLM backbone inventory and per-backbone availability diagnostics
- detector / rectify backend inventory and availability diagnostics
- service default backend settings for actual trial use
- runtime information
- aggregate counts (`plugin_count`, `backbone_count`, `available_backbone_count`, detector / rectify totals)

### `POST /analyze-document`

Multipart form upload endpoint for recognition-only analysis.

Purpose:
- frontend debugging
- attachment preview pages
- OCR/result inspection without business verification

Fields:

- `plugin_name` (required; `plugin` alias accepted)
- `file` (required)
- `ocr_backend` / `vlm_backend` / `detector_backend` / `rectify_backend` (optional)
- optional extracted-field overrides such as `patient_name`, `rest_start_date`, `rest_end_date`, `issue_date`

Response shape:

- `result` — full pipeline output
- `analysis` — normalized analysis object for UI rendering

Example:

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

### `POST /infer`

Multipart form upload endpoint.

Fields:

- `plugin_name` (required; `plugin` is accepted as an alias)
- `file` (required)
- `ocr_backend` (optional, default: service-configured default; full image recommendation: `paddleocr`)
- `vlm_backend` (optional, default: service-configured default; recommended: `mock`)
- `detector_backend` (optional, default: service-configured default; recommended: `pil`)
- `rectify_backend` (optional, default: service-configured default; recommended: `pil`)
- `failure_dir` (optional)

Status codes:

- `200 OK`: inference completed and returns `{ filename, content_type, result }`
- `400 Bad Request`: uploaded file is empty
- `404 Not Found`: requested `plugin_name` does not exist
- `422 Unprocessable Entity`: request validation failed, or the selected `ocr_backend` / `vlm_backend` is unknown or currently unavailable. The service now rejects these cases explicitly and returns the backend validation error message in `detail`; it no longer silently falls back to `mock` during `/infer`.

Example:

```bash
curl -X POST http://127.0.0.1:8000/infer \
  -F plugin_name=boarding_pass \
  -F ocr_backend=mock \
  -F vlm_backend=mock \
  -F detector_backend=pil \
  -F rectify_backend=pil \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

Current registered plugins include:

- `birth_certificate`
- `boarding_pass`
- `china_id`
- `custody_relationship_certificate`
- `diagnosis_proof`
- `hukou_booklet`
- `marriage_certificate`
- `medical_record`
- `only_child_certificate`
- `passport`
- `train_ticket`

`/infer` responses now include review-oriented payloads in addition to parsed fields:

- `quality.summary` and `quality.flags`
- `decision.action` (`accept`, `review`, or `reject`)
- `review.decision`, `review.warnings`, `review.evidence`
- unified `analysis` payload with:
  - `doc_type`
  - `doc_type_confidence`
  - `classification_evidence` (including rule-based leave-attachment label)
  - `extracted_fields`
  - `validation`, `review`, `risk`, `raw_artifacts`
- persisted failure-case metadata when `failure_dir` is configured and validation is not accepted

### `POST /verify-attachment`

Multipart form upload endpoint for leave-attachment verification.

Required fields:

- `plugin_name` (or `plugin` alias)
- `file`
- one of:
  - `expected_attachment_type`
  - `expected_attachment_types`
  - `leave_type`

Common request fields:

- `applicant_name`
- `related_person_name`
- `related_person_relation`
- `leave_start_date`
- `leave_end_date`
- any additional extracted-field overrides, such as `patient_name`, `rest_start_date`, `rest_end_date`, `issue_date`, `holder_name`, `person_a_name`, `person_b_name`

Response shape:

- `result` — the underlying pipeline result (same structure as `/infer`)
- `analysis` — the unified analysis payload copied from `result.analysis`
- `verification` — leave-business verification result with:
  - `verify_status` (`PASS`, `REVIEW`, `REJECT`)
  - `risk_score`, `risk_level`
  - `matched_attachment_type`
  - `rule_results`
  - `warnings`
  - `needs_manual_review`
  - `summary_message`

Example:

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

Marriage example:

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

## Run locally

```bash
pip install -e .
id-doc-ocr-api --host 0.0.0.0 --port 8000
```

Or:

```bash
id-doc-ocr serve --host 0.0.0.0 --port 8000
```

## Run with Docker

```bash
docker build -t id-doc-ocr .
docker run --rm -p 8000:8000 id-doc-ocr
```

The default image now installs PaddleOCR runtime dependencies too, so `GET /capabilities` should expose `paddleocr` as available. If you need a smaller image or Paddle wheels are unavailable for your target platform, build with `--build-arg ID_DOC_OCR_INSTALL_PADDLE=0` and stick to `rapidocr` / `mock`.

## Run with docker compose

```bash
cp .env.example .env
docker compose --env-file .env up --build -d
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/capabilities
curl -X POST http://127.0.0.1:8000/infer \
  -F plugin_name=birth_certificate \
  -F ocr_backend=paddleocr \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
open http://127.0.0.1:8080
```

Compose now starts two services together:

- API: `http://127.0.0.1:8000`
- UI lab: `http://127.0.0.1:8080`

The UI is a static page that calls the API directly, and the API enables cross-origin requests for local comparison use.

On Apple Silicon, Compose normally builds a `linux/arm64` image. If Paddle wheel resolution fails on your network or mirror, either set `ID_DOC_OCR_INSTALL_PADDLE=0` for a lighter image, or force x86 emulation with `DOCKER_DEFAULT_PLATFORM=linux/amd64`.

For the production-leaning compose flow, healthcheck, and supported runtime knobs, see [docs/deployment.md](deployment.md).
