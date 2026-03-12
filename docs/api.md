# API quickstart

The repo now exposes a minimal HTTP service for local development and container deployment.

For deployment and operational guidance beyond the endpoint examples here, see [deployment.md](deployment.md).

## Endpoints

### `GET /health`

Returns service liveness and the currently registered plugins.

### `POST /infer`

Multipart form upload endpoint.

Fields:

- `plugin_name` (required)
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
```

For the production-leaning compose flow, healthcheck, and supported runtime knobs, see [docs/deployment.md](deployment.md).
