# PaddleOCR-VL integration track

This repository now includes a concrete `PaddleOCRVLAdapter` path instead of a pure placeholder.

## What is implemented

- optional runtime detection (`paddleocr` import check)
- best-effort engine bootstrap using `PaddleOCRVL` first, then `PaddleOCR`
- graceful `unavailable` response when the runtime is missing
- output normalization into a stable shape:
  - `text`
  - `layout`
  - `kv`
  - `confidence`
  - `runtime`
- demo pipeline wiring via `DemoPipelineRunner(vlm_backend="auto" | "paddleocr_vl" | "mock")`

## Install

Minimal dev/test setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Enable the VLM path:

```bash
pip install -e .[paddle-vl]
```

Current extra pulls the common runtime pieces used by the adapter. Depending on the PaddleOCR release you target, you may still need to pin a version that exposes `PaddleOCRVL` or a compatible `PaddleOCR` API.

## Example

```bash
python examples/run_paddleocr_vl_demo.py
```

With runtime installed, the adapter will try real inference. Without it, the demo still runs and clearly reports `status=unavailable` or falls back to the mock VLM adapter in `auto` mode.

## Intended usage

Use PaddleOCR-VL as:

1. a fallback when deterministic field OCR misses fields
2. a backbone for weak-template documents like medical records or household booklets
3. a layout/KV extraction helper before validation and review routing

## Known gaps / TODO

- confirm and pin the exact PaddleOCR package/version for production use
- add fixture-based golden tests against a real installed runtime
- enrich normalization for tables, formulas, and nested layout blocks
- thread VLM-derived KV results back into plugin-level parsers and confidence fusion
