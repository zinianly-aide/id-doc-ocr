FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ID_DOC_OCR_FAILURE_DIR=/data/failures

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs
COPY examples ./examples

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    adduser --disabled-password --gecos "" appuser && \
    mkdir -p /data/failures && \
    chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["id-doc-ocr-api", "--host", "0.0.0.0", "--port", "8000"]
