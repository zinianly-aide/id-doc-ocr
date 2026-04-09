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

## Service API and deployment

A minimal HTTP service is now available with:

- `GET /health`
- `GET /capabilities`
- `POST /infer`
- local CLI serve entrypoint
- Dockerfile and `docker-compose.yml`
- `.env.example` and `Makefile` for repeatable compose-based startup

What the service now exposes beyond a bare liveness probe:

- plugin inventory for all registered document types
- OCR / VLM backbone availability details
- normalized quality / routing summary (`quality.summary`, `quality.flags`)
- review-oriented decision output (`decision`, `review`, `warnings`, `evidence`)
- optional failure-case persistence via `failure_dir`

Docs:

- API quickstart: [docs/api.md](docs/api.md)
- deployment / ops runbook: [docs/deployment.md](docs/deployment.md)

## Regression track

Public smoke-regression assets and fixture-based parser regression are documented in [docs/regression.md](docs/regression.md).

Current checked-in regression inventory:

- public assets: `35` samples in `examples/assets/manifest.json`
- parser fixtures: `17` fixtures across `birth_certificate`, `boarding_pass`, `china_id`, `custody_relationship_certificate`, `diagnosis_proof`, `hukou_booklet`, `medical_record`, `only_child_certificate`, `passport`, and `train_ticket`
- latest parser regression report: `reports/parser_regression_latest.json`
  - `17/17` fixtures passed
  - `140/140` expected fields matched
  - overall field exact-match rate: `1.00`

### Browser-based recognition spot-check (manual)

To complement fixture-based parser regression, we also did a small browser-driven visual spot-check against mixed public images. A first seed asset set for this track is now checked into `examples/assets/browser_visual/` and indexed in `examples/assets/manifest.json` with `benchmark_track="browser_visual_spotcheck"`.

| Sample type | Example | What the recognizer got right | Observed limitation |
| --- | --- | --- | --- |
| Receipt / OCR text | Walmart receipt | Merchant, timestamp, subtotal / tax / total, most item lines | Long IDs / approval codes remain higher-risk for small OCR slips |
| Natural image | Cat portrait | Main object, scene type, coarse visual attributes | Good for captioning / understanding, not structured extraction |
| Chart / diagram | Stacked bar chart | Chart type, title, legend, x-axis categories, most bar labels | Precise numeric extraction is less stable than pure OCR documents |
| UI screenshot | GitHub login page | Page purpose, key controls, field labels, CTA buttons | Layout understanding is good, but pixel-accurate validation should still rely on DOM / a11y data |
| Handwritten / formula-like | Paddle formula sample | Useful for testing non-standard glyph grouping and symbol reading | Not a clean proxy for true free-form handwriting |
| Dense table | TableBank sample | Good stress case for grid-heavy layouts and cell structure | Requires dedicated table extraction to go beyond coarse recognition |
| Noisy document | XFUND / KIE sample | Better stress on cluttered business-doc layout and mobile capture artifacts | Harder to score without task-specific expected outputs |
| Multilingual form | FUNSD / form-like sample | Useful for layout + key-value robustness beyond plain OCR | Needs plugin-specific evaluation if promoted from spot-check to hard benchmark |

Takeaway:

- strongest on text-heavy screenshots and clean documents
- reliable for general object / scene recognition
- usable for chart understanding, but not yet a substitute for dedicated chart-to-table extraction
- best used as a qualitative benchmark supplement, not as the primary parser regression signal

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
- [x] production-grade detector / rectify stages
- [x] broader document-specific parser + validator coverage
- [x] minimal deployment / ops docs for local, Docker, compose, and CI mapping

## CI

GitHub Actions is wired for:

- `pytest` on push / pull request to `main`
- Python 3.10 / 3.11 test matrix
- package build validation via `python -m build`
- Docker image build-only validation via `docker build --tag id-doc-ocr:ci .`

Workflow file: `.github/workflows/ci.yml`

## Current status snapshot

What is already in the repo today:

- demo pipeline runner with pluggable detector / OCR / VLM backbones
- working detector / rectify seams, plus `rapidocr`, `paddleocr`, and `paddleocr_vl` adapter paths
- detector seam with typed quad / classification contracts and a mock adapter ready for real model integration
- parser / validator coverage for boarding pass, train ticket, medical record, plus strengthened China ID / passport / hukou booklet flows
- newly added parser plugins for `birth_certificate`, `only_child_certificate`, `custody_relationship_certificate`, and `diagnosis_proof`
- MRZ parsing + validation utilities
- parser regression fixtures now cover `birth_certificate`, `boarding_pass`, `china_id` (front/back), `custody_relationship_certificate`, `diagnosis_proof`, `hukou_booklet`, `medical_record`, `only_child_certificate`, `passport` TD3 MRZ, and `train_ticket`
- evaluation report models and regression fixtures / smoke assets
- CLI entrypoint and dataset / failure-log helper tools
- service responses include review-ready quality / validation evidence suitable for human-in-the-loop routing

What is still intentionally incomplete:

- production detector / rectification implementation
- deployment-hardening beyond the current minimal service/Docker/compose runbook
- full end-to-end extraction coverage for every plugin listed in the repo

## License

MIT
