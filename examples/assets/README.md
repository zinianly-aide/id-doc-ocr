# Public Regression Assets

These assets are pulled from public example files in the PaddleOCR repository and grouped by document/content type for regression experiments.

## What this folder is for
- fast OCR smoke checks across mixed document styles
- parser/plugin regression fixtures
- annotation mapping checks
- public demo inputs for examples and docs

## Categories
- `boarding_pass/` - boarding-pass / ticket-like samples
- `browser_visual/` - browser-captured or browser-sourced mixed visual spot-check samples
- `captcha/` - captcha-like OCR samples
- `char_rec/` - tiny single-character recognition sample
- `doc/` - generic document-style samples
- `formula/` - formula / handwritten-like samples
- `layout/` - page-layout-heavy samples
- `license_plate/` - plate OCR sample
- `multilingual/` - multilingual form / KIE-style samples
- `receipt/` - receipt-style samples
- `seal/` - seal / stamped-document samples
- `street/` - scene text samples
- `table/` - table extraction samples

## Manifest notes
`manifest.json` is the source of truth for the smoke-regression runner.
Each sample records:
- `sample_id`
- `category`
- `kind`
- `path`
- `source_path`
- `source_url`
- `sha256`
- `size_bytes`
- `license`

This makes the checked-in assets easier to audit and refresh.

For `browser_visual/` samples, the manifest may also include `benchmark_track` to distinguish manual browser-oriented spot-check assets from the original PaddleOCR-sourced smoke-regression pool.

## Reports
- `python examples/run_asset_smoke_regression.py`
- `python examples/run_parser_regression.py`

Both write JSON reports into `reports/`.
