# P1-P5 Hardening Implementation Plan

> For Hermes: implement this plan incrementally with tests after each logical slice.

Goal: strengthen detector/rectify realism, upgrade the pipeline/service surface, document plugin maturity, improve local developer UX, and expand service API regression coverage.

Architecture: keep the existing plugin-based OCR platform intact while replacing hardcoded mock detector/rectify wiring with configurable backends. Use a minimal classical-CV style path for detector/rectify so the system gains real image-aware behavior without requiring model training. Align docs, tests, and startup flows around a single supported local-dev path.

Tech Stack: Python, FastAPI, Pydantic v2, pytest, optional OpenCV/Pillow-compatible image processing fallback.

---

## Phase 1
- Add image-aware detector + rectify backends with graceful dependency fallback
- Make runner/service expose detector/rectify backend selection and capability inventory

## Phase 2
- Add plugin maturity inventory + docs output
- Improve Makefile/.env/docs for one-command dev/test/service startup

## Phase 3
- Expand service API regression coverage for defaults, env propagation, error details, and backend routing

## Verification
- Run targeted pytest files for detector/rectify/service
- Run a full focused pytest slice covering touched areas
- Check git diff for docs/code consistency
