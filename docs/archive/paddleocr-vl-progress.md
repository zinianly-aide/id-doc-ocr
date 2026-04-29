# PaddleOCR-VL progress note

Date: 2026-03-11

## Completed

- replaced placeholder `PaddleOCRVLAdapter` with a concrete optional-runtime adapter
- added runtime detection and graceful unavailable-mode behavior
- wired VLM backend selection into `DemoPipelineRunner`
- added demo script and setup documentation
- added unit tests for normalization, fallback behavior, and runner wiring

## Current blocker

This workspace does not currently have `paddleocr` installed, so real PaddleOCR-VL inference could not be executed end-to-end here.

## Next step when runtime is available

1. install `pip install -e .[paddle-vl]`
2. verify which PaddleOCR release exposes the production-ready VL API (`PaddleOCRVL` vs compatible `PaddleOCR` path)
3. capture golden outputs on real complex-document samples
4. feed normalized `kv`/layout output into plugin-specific fallback parsing and confidence fusion
