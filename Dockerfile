ARG ID_DOC_OCR_PYTHON_BASE_IMAGE=python:3.11-slim-bookworm
FROM ${ID_DOC_OCR_PYTHON_BASE_IMAGE}

ARG ID_DOC_OCR_INSTALL_PADDLE=1
ARG ID_DOC_OCR_PYTHON_BASE_IMAGE
ARG ID_DOC_OCR_APT_MIRROR=http://deb.debian.org/debian
ARG ID_DOC_OCR_APT_SECURITY_MIRROR=http://deb.debian.org/debian-security
ARG ID_DOC_OCR_PIP_INDEX_URL=https://pypi.org/simple
ARG ID_DOC_OCR_PIP_EXTRA_INDEX_URL=
ARG ID_DOC_OCR_PIP_TRUSTED_HOST=
ARG ID_DOC_OCR_PREFETCH_PADDLE_MODELS=0
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG http_proxy
ARG https_proxy
ARG no_proxy

WORKDIR /app

RUN python3 - <<'PY'
from pathlib import Path
import os

mirror = os.environ.get('ID_DOC_OCR_APT_MIRROR', 'http://deb.debian.org/debian')
security = os.environ.get('ID_DOC_OCR_APT_SECURITY_MIRROR', 'http://deb.debian.org/debian-security')
for path in [Path('/etc/apt/sources.list'), *Path('/etc/apt/sources.list.d').glob('*.sources')]:
    if not path.exists():
        continue
    text = path.read_text()
    text = text.replace('http://deb.debian.org/debian-security', security)
    text = text.replace('http://deb.debian.org/debian', mirror)
    path.write_text(text)
PY

RUN apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=20 && \
    apt-get install -y --no-install-recommends \
      -o Acquire::Retries=5 \
      -o Acquire::http::Timeout=20 \
      --fix-missing \
      libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ID_DOC_OCR_FAILURE_DIR=/data/failures \
    ID_DOC_OCR_PADDLE_MODEL_CACHE_DIR=/home/appuser/.paddlex \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
    PIP_INDEX_URL=${ID_DOC_OCR_PIP_INDEX_URL} \
    PIP_EXTRA_INDEX_URL=${ID_DOC_OCR_PIP_EXTRA_INDEX_URL} \
    PIP_TRUSTED_HOST=${ID_DOC_OCR_PIP_TRUSTED_HOST}

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs
COPY examples ./examples
COPY docker ./docker

RUN if [ "$ID_DOC_OCR_INSTALL_PADDLE" = "1" ]; then \
      pip install --no-cache-dir --no-build-isolation '.[ocr,paddle-vl]' paddlepaddle==3.0.0; \
    else \
      pip install --no-cache-dir --no-build-isolation '.[ocr]'; \
    fi && \
    adduser --disabled-password --gecos "" appuser && \
    mkdir -p /data/failures /home/appuser/.paddlex && \
    chown -R appuser:appuser /app /data /home/appuser

RUN if [ "$ID_DOC_OCR_INSTALL_PADDLE" = "1" ] && [ "$ID_DOC_OCR_PREFETCH_PADDLE_MODELS" = "1" ]; then \
      su -s /bin/sh appuser -c "cd /app && python docker/prefetch_paddle_models.py"; \
    fi

USER appuser

EXPOSE 8000

CMD ["id-doc-ocr-api", "--host", "0.0.0.0", "--port", "8000"]
