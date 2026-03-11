# Regression assets and reports

This repo keeps a small public regression track under `examples/assets/` and `examples/fixtures/`.

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

Report: `reports/parser_regression_latest.json`

Current report structure includes:
- report metadata
- runner metadata
- totals (`num_fixtures`, `num_passed`, `num_failed`, field totals, overall status)
- per-fixture pass/fail status
- field-by-field exact-match details

## Updating the asset set

When adding a public sample:
1. copy the asset into the right category folder under `examples/assets/`
2. add a manifest entry with provenance and checksum fields
3. rerun asset smoke regression
4. if the sample is useful for a plugin, add an expected fixture under `examples/fixtures/`
5. rerun parser regression

## Notes

- The checked-in manifest is the audit surface; keep it readable.
- Prefer public upstream examples with stable raw URLs.
- Duplicates are okay only when they serve a specific parser fixture path; otherwise prefer unique samples.
