# API quickstart

The repo now exposes a minimal HTTP service for local development and container deployment.

For deployment and operational guidance beyond the endpoint examples here, see [deployment.md](deployment.md).

## Endpoints

### `GET /health`

Returns service liveness plus a lightweight runtime snapshot:

- service name / version
- registered plugin names
- backbone availability summary
- runtime metadata
- default failure directory

### `GET /capabilities`

Returns the fuller machine-readable inventory used for readiness checks and UI bootstrapping:

- plugin metadata (`name`, `schema`, `tags`, supported backbones)
- OCR / VLM backbone inventory and per-backbone availability diagnostics
- runtime information
- aggregate counts (`plugin_count`, `backbone_count`, `available_backbone_count`)

### `POST /infer`

Multipart form upload endpoint.

Fields:

- `plugin_name` (required; `plugin` is accepted as an alias)
- `file` (required)
- `ocr_backend` (optional, default: `mock`)
- `vlm_backend` (optional, default: `auto`)
- `failure_dir` (optional)

Example:

```bash
curl -X POST http://127.0.0.1:8000/infer \
  -F plugin_name=boarding_pass \
  -F ocr_backend=mock \
  -F vlm_backend=mock \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

Current registered plugins include:

- `birth_certificate`
- `boarding_pass`
- `china_id`
- `custody_relationship_certificate`
- `diagnosis_proof`
- `hukou_booklet`
- `medical_record`
- `only_child_certificate`
- `passport`
- `train_ticket`

`/infer` responses now include review-oriented payloads in addition to parsed fields:

- `quality.summary` and `quality.flags`
- `decision.action` (`accept`, `review`, or `reject`)
- `review.decision`, `review.warnings`, `review.evidence`
- persisted failure-case metadata when `failure_dir` is configured and validation is not accepted

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

## Run with docker compose

```bash
cp .env.example .env
docker compose --env-file .env up --build -d
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/capabilities
curl -X POST http://127.0.0.1:8000/infer \
  -F plugin_name=birth_certificate \
  -F ocr_backend=mock \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

For the production-leaning compose flow, healthcheck, and supported runtime knobs, see [docs/deployment.md](deployment.md).
