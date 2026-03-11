# id-doc-ocr

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

## Architecture

See [docs/architecture.md](docs/architecture.md).

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
- [ ] first end-to-end pipeline interfaces
- [ ] Chinese resident ID extraction schema
- [ ] passport MRZ parser + validator
- [ ] baseline evaluation harness
- [ ] service API and deployment manifests

## License

MIT
