# id-doc-ocr

[English](README.md) | [简体中文](docs/zh/README.zh-CN.md)

A self-hosted OCR system for identity documents with a production-oriented architecture:

- document detection and classification
- geometric rectification and image quality checks
- field-level OCR
- KIE / VLM fallback for weak-template scenarios
- MRZ / barcode / checksum validation
- human review for low-confidence cases

## Goals

- high field-level exact-match accuracy for ID documents
- explainable, auditable extraction pipeline
- modular architecture for gradual optimization
- self-hosted deployment

## Proposed stack

- **Primary OCR backbone**: PaddleOCR family
- **Complex document / weak-template enhancement**: PaddleOCR-VL
- **Region fallback OCR**: GOT-OCR 2.0
- **Validation**: rule engine for dates, document numbers, MRZ, cross-field consistency

## Quick start by language

- **English project guide**: this page
- **Chinese project guide**: [docs/zh/README.zh-CN.md](docs/zh/README.zh-CN.md)

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Service API

A minimal HTTP service is now available with:

- `GET /health`
- `POST /infer`
- local CLI serve entrypoint
- Dockerfile and `docker-compose.yml`

See [docs/api.md](docs/api.md).

## Regression track

Public smoke-regression assets and fixture-based parser regression are documented in [docs/regression.md](docs/regression.md).

## PaddleOCR-VL track

The repository now includes a concrete PaddleOCR-VL integration path with:

- optional runtime detection
- normalized VLM output (`text`, `layout`, `kv`, `confidence`)
- demo runner wiring with `vlm_backend="auto"`
- graceful fallback when Paddle runtime is not installed

Setup and caveats: [docs/paddleocr-vl.md](docs/paddleocr-vl.md).

## OCR backbones today

- `mock`: default lightweight stub for pipeline development
- `rapidocr`: working ONNX runtime baseline for local smoke tests
- `paddleocr`: concrete adapter layer with lazy runtime import, normalization, and demo wiring

For PaddleOCR local setup and environment knobs, see [docs/paddleocr-setup.md](docs/paddleocr-setup.md).

## Initial scope

Phase 1 focuses on:

1. repository scaffold
2. architecture and interfaces
3. Chinese ID card support
4. passport MRZ support
5. evaluation pipeline and benchmark datasets

## Repository layout

```text
src/id_doc_ocr/
  detector/     # document detection, corner detection, doc classification
  rectify/      # perspective correction, orientation, quality scoring
  ocr/          # OCR adapters and field-level recognition
  kie/          # key information extraction / VLM fallback
  validator/    # MRZ, checksum, rules, consistency checks
  review/       # human-in-the-loop review primitives
  pipeline/     # orchestration and stage composition
  schemas/      # typed document/result schemas
  utils/        # shared helpers
```

## Roadmap

- [x] architecture skeleton
- [x] first end-to-end pipeline interfaces
- [x] Chinese resident ID extraction schema
- [x] passport MRZ parser + validator
- [x] baseline evaluation harness
- [x] service API and deployment manifests
- [ ] production-grade detector / rectify stages
- [ ] broader document-specific parser + validator coverage
- [ ] deployment-ready service layer and ops docs

## CI

GitHub Actions is wired for:

- `pytest` on push / pull request to `main`
- Python 3.10 / 3.11 test matrix
- package build validation via `python -m build`

Workflow file: `.github/workflows/ci.yml`

## Current status snapshot

What is already in the repo today:

- demo pipeline runner with pluggable OCR / VLM backbones
- working `rapidocr`, `paddleocr`, and `paddleocr_vl` adapter paths
- parser / validator coverage for boarding pass, train ticket, medical record, hukou booklet, and baseline passport / China ID pieces
- MRZ parsing + validation utilities
- evaluation report models and regression fixtures / smoke assets
- CLI entrypoint and dataset / failure-log helper tools

What is still intentionally incomplete:

- production detector / rectification implementation
- service API, deployment manifests, and operations workflow
- full end-to-end extraction coverage for every plugin listed in the repo

## License

MIT
