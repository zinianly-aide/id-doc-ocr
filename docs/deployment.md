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

- `ID_DOC_OCR_PYTHON_BASE_IMAGE=python:3.11-slim-bookworm`: default base image for normal builds
- if Docker Hub pulls time out but you already have a compatible Python base image cached locally, tag it (for example `docker tag python:3.11-slim local/python:3.11-slim`) and set `ID_DOC_OCR_PYTHON_BASE_IMAGE=local/python:3.11-slim`
- `ID_DOC_OCR_APT_MIRROR=http://deb.debian.org/debian`: main Debian package mirror used during image build (HTTPS mirrors are preferred when available for safer transport)
- `ID_DOC_OCR_APT_SECURITY_MIRROR=http://deb.debian.org/debian-security`: Debian security mirror used during image build (HTTPS mirrors are preferred when available for safer transport)
- `ID_DOC_OCR_PIP_INDEX_URL=https://pypi.org/simple`: pip package index used during image build
- `ID_DOC_OCR_PIP_EXTRA_INDEX_URL`: optional secondary package index
- `ID_DOC_OCR_PIP_TRUSTED_HOST`: only needed for non-default trust scenarios; avoid unless required
- `ID_DOC_OCR_PREFETCH_PADDLE_MODELS=0`: when set to `1` during a full Paddle build, run one sample inference at build time so OCR runtime models are baked into the image layer/cache
- `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`: optional proxy passthrough for build and runtime when Docker Desktop is not already configured with a proxy
- `ID_DOC_OCR_INSTALL_PADDLE=1` (default): build the full image with PaddleOCR enabled
- `ID_DOC_OCR_INSTALL_PADDLE=0`: build a lighter `rapidocr` / `mock` image when Paddle wheels are not available or you want faster builds
- `ID_DOC_OCR_DEFAULT_OCR_BACKEND=paddleocr`: recommended full-image runtime default
- `ID_DOC_OCR_DEFAULT_VLM_BACKEND=mock`: recommended stable default for practical trials
- `ID_DOC_OCR_DEFAULT_DETECTOR_BACKEND=pil`
- `ID_DOC_OCR_DEFAULT_RECTIFY_BACKEND=pil`
- `ID_DOC_OCR_PADDLE_MODEL_CACHE_DIR_HOST=./data/paddle-model-cache`: host directory mounted to `/home/appuser/.paddlex` so official model downloads survive container restarts

Mirror troubleshooting:

- on this machine, Docker already has daemon-level proxy settings (`http.docker.internal:3128`), so adding another system proxy is usually not the first fix
- the more promising mitigation is switching Debian mirrors when `apt-get update` / `apt-get install` is slow or returns transient 502s
- two candidate mirrors that responded faster than `deb.debian.org` in local checks were:
  - `https://mirrors.tuna.tsinghua.edu.cn/debian`
  - `https://mirrors.aliyun.com/debian`
- matching security mirrors:
  - `https://mirrors.tuna.tsinghua.edu.cn/debian-security`
  - `https://mirrors.aliyun.com/debian-security`

Example `.env` override for mainland-friendly mirrors:

```bash
ID_DOC_OCR_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian
ID_DOC_OCR_APT_SECURITY_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian-security
ID_DOC_OCR_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

PyPI mirror troubleshooting:

- local latency checks showed these HTTPS mirrors were much faster than `https://pypi.org/simple` on this machine:
  - `https://pypi.tuna.tsinghua.edu.cn/simple`
  - `https://mirrors.aliyun.com/pypi/simple`
  - `https://pypi.mirrors.ustc.edu.cn/simple`
- prefer HTTPS mirrors so we do not need to weaken trust settings with `trusted-host`

Apple Silicon / ARM notes:

- Docker Desktop on Apple Silicon builds `linux/arm64` images by default; current Paddle wheels worked in local validation on that target
- the first real PaddleOCR request may download model assets, so expect the first `/infer?ocr_backend=paddleocr` call to be slower than later calls
- if your host / mirror cannot resolve compatible Paddle wheels, rebuild with `ID_DOC_OCR_INSTALL_PADDLE=0` and use `rapidocr` or `mock` as the OCR backend
- if you specifically need x86 wheels on Apple Silicon, run compose with emulation, for example `DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up --build`

## Re-verified full Paddle build path

This exact fallback path was re-tested locally after Docker Hub timeouts blocked `python:3.11-slim-bookworm` metadata fetches:

```bash
/opt/homebrew/bin/python3.11 -m pytest -q
docker compose --env-file .env.example config

docker build \
  --build-arg ID_DOC_OCR_PYTHON_BASE_IMAGE=python:3.11-slim \
  --build-arg ID_DOC_OCR_INSTALL_PADDLE=1 \
  --build-arg ID_DOC_OCR_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian \
  --build-arg ID_DOC_OCR_APT_SECURITY_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian-security \
  --build-arg ID_DOC_OCR_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  -t id-doc-ocr:full-verify .

docker run -d --name id-doc-ocr-full-verify-run \
  -p 18001:8000 \
  -e ID_DOC_OCR_DEFAULT_OCR_BACKEND=paddleocr \
  -e ID_DOC_OCR_DEFAULT_VLM_BACKEND=mock \
  -e ID_DOC_OCR_DEFAULT_DETECTOR_BACKEND=pil \
  -e ID_DOC_OCR_DEFAULT_RECTIFY_BACKEND=pil \
  id-doc-ocr:full-verify

curl http://127.0.0.1:18001/health
curl http://127.0.0.1:18001/capabilities
curl -X POST http://127.0.0.1:18001/infer \
  -F plugin=boarding_pass \
  -F ocr_backend=paddleocr \
  -F vlm_backend=mock \
  -F detector_backend=pil \
  -F rectify_backend=pil \
  -F file=@examples/assets/paddle_sample_doc_00006737.jpg

docker rm -f id-doc-ocr-full-verify-run
```

Observed successful result from the real sample inference:

- `passenger_name=ZHANGQIWEI`
- `flight_number=MU2379`

## Recommended performance optimizations for full Paddle deployments

Fastest practical setup without rebuilding often:

```bash
mkdir -p data/failures data/paddle-model-cache
cp .env.example .env
# keep the persistent model cache mount enabled
docker compose up --build
```

This stores official Paddle/PaddleX model downloads under `./data/paddle-model-cache`, so after the first successful inference, later restarts do not need to re-download those models.

If you want the image itself to arrive pre-warmed for first-use demos or CI images, enable build-time prefetch:

```bash
ID_DOC_OCR_INSTALL_PADDLE=1 \
ID_DOC_OCR_PREFETCH_PADDLE_MODELS=1 \
ID_DOC_OCR_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
ID_DOC_OCR_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian \
ID_DOC_OCR_APT_SECURITY_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian-security \
  docker compose build api
```

Trade-offs:

- persistent cache mount:
  - best default for local/dev and long-lived hosts
  - faster subsequent startups and first inference after restart
  - image size stays smaller than a prewarmed image
- build-time prefetch:
  - best when you want a ready-to-demo image artifact
  - slower build
  - larger image layers
  - still benefits from the mounted cache if you keep the volume enabled at runtime

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
