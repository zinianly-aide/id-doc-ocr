FROM python:3.11-slim

ARG ID_DOC_OCR_INSTALL_PADDLE=1

WORKDIR /app

RUN apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=20 && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ID_DOC_OCR_FAILURE_DIR=/data/failures \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs
COPY examples ./examples

RUN if [ "$ID_DOC_OCR_INSTALL_PADDLE" = "1" ]; then \
      pip install --no-cache-dir --no-build-isolation '.[ocr,paddle-vl]' paddlepaddle; \
    else \
      pip install --no-cache-dir --no-build-isolation '.[ocr]'; \
    fi && \
    adduser --disabled-password --gecos "" appuser && \
    mkdir -p /data/failures && \
    chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["id-doc-ocr-api", "--host", "0.0.0.0", "--port", "8000"]
