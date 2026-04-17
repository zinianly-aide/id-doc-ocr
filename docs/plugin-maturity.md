# Plugin maturity inventory

This project now exposes plugin maturity metadata through `GET /capabilities` so operators can tell which document types are safest to trial in Docker.

## What the inventory includes

For each plugin, the service reports:

- `maturity.level`
  - `production_candidate`
  - `beta`
  - `experimental`
- `maturity.reason`
- `regression`
  - fixture count
  - live-image fixture count
  - expected field count
  - latest parser regression status
  - latest field exact-match rate
- `trial_profile`
  - recommended `ocr_backend`
  - recommended `vlm_backend`
  - recommended `detector_backend`
  - recommended `rectify_backend`

## Current interpretation

- `production_candidate`
  - multiple fixtures pass
  - at least one live-image fixture exists
  - latest parser regression is passing with very high field exact match
- `beta`
  - parser regression passes with fixture coverage
  - but live-image breadth or fixture depth is still limited
- `experimental`
  - limited regression evidence or incomplete fixture coverage

## Docker trial recommendation

For the full Docker image (`ID_DOC_OCR_INSTALL_PADDLE=1`):

- default `ocr_backend`: `paddleocr`
- default `vlm_backend`: `mock`
- default `detector_backend`: `pil`
- default `rectify_backend`: `pil`

For the lighter image (`ID_DOC_OCR_INSTALL_PADDLE=0`):

- switch `ID_DOC_OCR_DEFAULT_OCR_BACKEND=rapidocr`
- keep `vlm_backend=mock`
- keep `detector_backend=pil`
- keep `rectify_backend=pil`

## Why this matters

Not every plugin has the same readiness profile. Some are parser-strong but still rely mostly on text fixtures; others already have at least one live-image regression case. The maturity inventory helps you choose which plugin to try first in real Docker-backed validation runs.
