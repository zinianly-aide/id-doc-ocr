# Deployment notes

This repo now includes a small Docker Compose setup for running the API and a lightweight UI lab together.

## Files

- `Dockerfile`: API container image build, now running as a non-root user
- `docker-compose.yml`: two-service stack, volume mount, env-driven port selection, and HTTP healthchecks
- `ui/index.html`: minimal comparison UI for uploads and result inspection
- `.env.example`: runtime knobs to copy into `.env`
- `Makefile`: common deploy / validation commands

## First run

```bash
cp .env.example .env
mkdir -p data/failures
make compose-config
make up
make health
make ui-health
curl http://127.0.0.1:${ID_DOC_OCR_PORT:-8000}/capabilities
curl -X POST http://127.0.0.1:${ID_DOC_OCR_PORT:-8000}/infer \
  -F plugin_name=boarding_pass \
  -F ocr_backend=mock \
  -F vlm_backend=mock \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

Addresses after startup:

- API: `http://127.0.0.1:${ID_DOC_OCR_PORT:-8000}`
- UI lab: `http://127.0.0.1:${ID_DOC_OCR_UI_PORT:-8080}`

## Runtime data

Failed samples or diagnostics can be written to the mounted host directory configured by `ID_DOC_OCR_FAILURE_DIR`.

## Useful commands

```bash
make ps
make logs
make down
```

## Healthcheck

Docker Compose uses:

- API container probe: `GET /health`
- UI container probe: `GET /index.html`

For deployment validation after startup, also verify:

- `GET /capabilities`
- `POST /infer`
- browser access to the UI lab
- UI fetches to API from `http://127.0.0.1:8000` with CORS enabled in the FastAPI service
