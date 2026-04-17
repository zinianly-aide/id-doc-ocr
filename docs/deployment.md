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
  -F ocr_backend=paddleocr \
  -F vlm_backend=mock \
  -F detector_backend=pil \
  -F rectify_backend=pil \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg
```

Addresses after startup:

- API: `http://127.0.0.1:${ID_DOC_OCR_PORT:-8000}`
- UI lab: `http://127.0.0.1:${ID_DOC_OCR_UI_PORT:-8080}`

## Runtime data

Failed samples or diagnostics can be written to the mounted host directory configured by `ID_DOC_OCR_FAILURE_DIR`.

## Docker OCR runtime notes

The image now installs `rapidocr`, `paddleocr`, and `paddlepaddle` by default, so `/capabilities` should report `paddleocr` as available inside the API container.

Useful knobs:

- `ID_DOC_OCR_INSTALL_PADDLE=1` (default): build the full image with PaddleOCR enabled
- `ID_DOC_OCR_INSTALL_PADDLE=0`: build a lighter `rapidocr` / `mock` image when Paddle wheels are not available or you want faster builds
- `ID_DOC_OCR_DEFAULT_OCR_BACKEND=paddleocr`: recommended full-image runtime default
- `ID_DOC_OCR_DEFAULT_VLM_BACKEND=mock`: recommended stable default for practical trials
- `ID_DOC_OCR_DEFAULT_DETECTOR_BACKEND=pil`
- `ID_DOC_OCR_DEFAULT_RECTIFY_BACKEND=pil`

Apple Silicon / ARM notes:

- Docker Desktop on Apple Silicon builds `linux/arm64` images by default; current Paddle wheels worked in local validation on that target
- the first real PaddleOCR request may download model assets, so expect the first `/infer?ocr_backend=paddleocr` call to be slower than later calls
- if your host / mirror cannot resolve compatible Paddle wheels, rebuild with `ID_DOC_OCR_INSTALL_PADDLE=0` and use `rapidocr` or `mock` as the OCR backend
- if you specifically need x86 wheels on Apple Silicon, run compose with emulation, for example `DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up --build`

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
