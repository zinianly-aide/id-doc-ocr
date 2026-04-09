# Regression assets and reports

This repo keeps a small public regression track under `examples/assets/` and `examples/fixtures/`.

Current parser fixtures intentionally bias toward stable document types and include:
- `birth_certificate`: de-identified text fixture
- `boarding_pass`: public sample image fixture
- `china_id`: front/back inline OCR fixtures plus a multiline-address + lowercase-`x` boundary fixture
- `custody_relationship_certificate`: de-identified guardianship / custody text fixture
- `diagnosis_proof`: text-rich and minimal diagnosis certificate fixtures
- `passport`: TD3 MRZ inline OCR fixtures, including a text-fallback + `«` normalization + unspecified-sex boundary fixture
- `hukou_booklet`: labeled household member card fixture plus a standalone-labels + inferred-birth boundary fixture
- `train_ticket`: inline OCR fixtures, including a NAME-anchor proximity boundary fixture
- `medical_record`: outpatient-note and sick-note-like inline text fixtures
- `only_child_certificate`: de-identified Shanghai-style certificate fixture

Current checked-in inventory snapshot:
- `examples/assets/manifest.json`: `35` public assets
- `examples/fixtures/`: `17` parser fixtures
- latest parser regression report (`reports/parser_regression_latest.json`): `17/17` fixtures passed, `140/140` expected fields matched

## Asset smoke regression

Purpose: catch broad OCR regressions quickly across a mixed public asset set.

Run:

```bash
PYTHONPATH=src ./.venv/bin/python examples/run_asset_smoke_regression.py
```

Report: `reports/asset_smoke_regression_latest.json`

Current report structure includes:
- report metadata (`schema_version`, `report_name`, `generated_at`)
- runner metadata (`ocr_backend`, `manifest_path`)
- manifest metadata (`name`, `version`, `source`, `num_samples`)
- totals (`num_processed`, `num_errors`, `status`)
- grouped summary (`by_category`, `by_kind`)
- per-sample results with `sha256`, `size_bytes`, `num_lines`, `confidence`, and `text_preview`
- explicit `errors` list for missing/broken assets

## Parser regression

Purpose: keep parser fixtures stable for known public samples.

Run:

```bash
PYTHONPATH=src ./.venv/bin/python examples/run_parser_regression.py
```

The checked-in runner now includes the newer `birth_certificate`, `custody_relationship_certificate`, `diagnosis_proof`, `medical_record/sick_note_like`, and `only_child_certificate` fixtures, so the generated report matches the full current fixture inventory.

Report: `reports/parser_regression_latest.json`

Current report structure includes:
- report metadata
- runner metadata
- totals (`num_fixtures`, `num_passed`, `num_failed`, field totals, overall status)
- per-fixture pass/fail status
- field-by-field exact-match details

This makes parser regression suitable both as a hard gate for stable template parsers and as a sanity check that newly added plugin families remain wired into the public regression story.

## Backbone benchmark template

Purpose: compare OCR/VLM backend combinations with a fixed, human-readable case list and a stable report format.

Seed manifest: `examples/backbone_benchmark_manifest.json`

Current seed design:
- `live_image`: one real image-backed boarding-pass case from `examples/assets/`
- `synthetic_control`: parser/validator control cases with inline `ocr_result`, used to verify downstream logic stays stable while OCR backbones change

Run:

```bash
PYTHONPATH=src ./.venv/bin/python examples/run_backbone_benchmark.py
```

Custom backend matrix example:

```bash
PYTHONPATH=src ./.venv/bin/python examples/run_backbone_benchmark.py \
  --backend mock:mock \
  --backend rapidocr:mock \
  --backend paddleocr:mock
```

Reports:
- JSON: `reports/backbone_benchmark_latest.json`
- Markdown: `reports/backbone_benchmark_latest.md`

Current benchmark summary fields:
- success rate
- validator accepted rate
- average warning count
- average validator issue count
- key-field hits / total / hit rate
- decision distribution
- per-case details for later diffing

Interpretation notes:
- `live_image` is the real backend comparison slice
- `synthetic_control` is backend-agnostic by design and acts as a parser/validator control group
- if a synthetic control regresses, the issue is probably downstream of OCR
- if only `live_image` regresses, the issue is more likely in OCR backbone behavior or OCR-to-parser coupling

## Updating the asset set

When adding a public sample:
1. copy the asset into the right category folder under `examples/assets/`
2. add a manifest entry with provenance and checksum fields
3. rerun asset smoke regression
4. if the sample is useful for a plugin, add an expected fixture under `examples/fixtures/`
5. rerun parser regression

## Browser-based visual spot-check

Purpose: supplement fixture-based parser regression with a small manual benchmark that exercises browser-captured images outside the main parser path.

This check is intentionally qualitative. It is useful for validating broad recognition behavior, but it should not replace field-level parser fixtures.

Current manual spot-check buckets:
- `receipt / OCR text`
- `natural image`
- `chart / diagram`
- `UI screenshot`
- `handwritten / formula-like`
- `dense table`
- `noisy document photo / scan`
- `multilingual form`

A first seed asset set for this track is now checked in under `examples/assets/browser_visual/` and indexed in `examples/assets/manifest.json` via `benchmark_track="browser_visual_spotcheck"`.

Observed results from the latest spot-check:

| Bucket | Example | Strength | Limitation |
| --- | --- | --- | --- |
| Receipt / OCR text | Walmart receipt | Strong on merchant / totals / timestamps / line items | Dense long numbers remain error-prone |
| Natural image | Cat portrait | Stable object / scene understanding | Not a structured extraction benchmark |
| Chart / diagram | Stacked penguin bar chart | Good title / legend / category understanding | Exact numeric extraction is weaker than document OCR |
| UI screenshot | GitHub login page | Strong page-purpose and control recognition | For automation-grade validation, DOM / accessibility data is still preferred |

Recommended use:
1. keep parser regression as the hard gate for structured extraction
2. use browser spot-checks as a soft signal for general visual robustness
3. if a browser sample reveals a stable failure mode, convert it into either:
   - a public asset in `examples/assets/`, or
   - a parser fixture in `examples/fixtures/` when it maps cleanly to a plugin

## Suggested benchmark expansion

If the repo grows a broader benchmark track, prefer adding samples in buckets like:
- clean receipts / invoices
- noisy mobile document photos
- tables with merged cells
- charts with dense labels
- multilingual forms
- login / settings / dashboard screenshots
- handwritten or low-contrast text

For each added sample, record:
- provenance URL
- license
- checksum
- expected benchmark focus (OCR, layout, chart reading, UI semantics, etc.)

## Notes

- The checked-in manifest is the audit surface; keep it readable.
- Prefer public upstream examples with stable raw URLs.
- Duplicates are okay only when they serve a specific parser fixture path; otherwise prefer unique samples.
