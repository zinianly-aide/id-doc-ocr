# Deployment notes

This repo now includes a small, production-leaning Docker Compose setup for running the API service persistently.

## Files

- `Dockerfile`: container image build, now running as a non-root user
- `docker-compose.yml`: restart policy, volume mount, env-driven port selection, and HTTP healthcheck
- `.env.example`: runtime knobs to copy into `.env`
- `Makefile`: common deploy / validation commands

## First run

```bash
cp .env.example .env
mkdir -p data/failures
make compose-config
make up
make health
```

The API should be reachable at `http://127.0.0.1:${ID_DOC_OCR_PORT:-8000}`.

## Runtime data

Failed samples or diagnostics can be written to the mounted host directory configured by `ID_DOC_OCR_FAILURE_DIR`.

## Useful commands

```bash
make ps
make logs
make down
```

## Healthcheck

Docker Compose uses the in-container Python runtime to probe:

- `GET /health`

That avoids adding extra packages such as `curl` only for liveness checks.
