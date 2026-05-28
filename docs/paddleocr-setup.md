# PaddleOCR setup

This repo now includes a concrete `PaddleOCRAdapter` integration layer, but it still treats PaddleOCR as an optional local runtime dependency.

## What is implemented

- lazy runtime import of `paddleocr`
- normalized adapter output: `engine`, `text`, `lines`, `confidence`
- environment-based config knobs for quick local experiments
- demo runner wiring via `DemoPipelineRunner(ocr_backend="paddleocr")`
- unit tests that validate normalization and runtime checks without requiring a heavyweight install in CI

## Local install options

For Docker / Compose, the repo now builds an image with `paddleocr` + pinned `paddlepaddle==3.0.0` by default. If you need a lighter image or your target platform cannot resolve Paddle wheels, set `ID_DOC_OCR_INSTALL_PADDLE=0` during build and use `rapidocr` or `mock` instead.

Requirements observed on this machine:

- Python `>=3.10` (the project metadata already requires this; a Python 3.9 venv will not satisfy the package)
- `paddleocr` alone is not enough for real inference; you also need a matching `paddlepaddle` runtime

Pick one of these approaches depending on how heavy you want the environment to be.

### Option A: project extras

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e '.[dev,paddle]'
pip install paddlepaddle==3.0.0
```

### Option B: manual install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e '.[dev]'
pip install paddleocr paddlepaddle==3.0.0
```

If your platform cannot resolve `paddlepaddle==3.0.0`, use Docker with `ID_DOC_OCR_INSTALL_PADDLE=0` and switch OCR backend to `rapidocr`/`mock`, or provide a compatible mirror/index that hosts this version.

## Environment knobs

- `ID_DOC_OCR_PADDLE_LANG` — default `ch`
- `ID_DOC_OCR_PADDLE_USE_ANGLE_CLS` — default `1`
- `ID_DOC_OCR_PADDLE_ENABLE_MKLDNN` — default `0`

Example:

```bash
export ID_DOC_OCR_PADDLE_LANG=en
export ID_DOC_OCR_PADDLE_USE_ANGLE_CLS=1
export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
python examples/run_paddleocr_demo.py
```

Notes from local validation:

- with PaddleOCR 3.x, the adapter now translates the repo's legacy config knobs to the newer constructor/inference API
- first run downloads model assets into `~/.paddlex/official_models/`
- if your environment routes HTTPS through a SOCKS proxy, you may also need `pip install 'httpx[socks]'`

## Demo usage

Direct adapter:

```bash
python examples/run_paddleocr_demo.py
```

Pipeline runner:

```python
from pathlib import Path
from id_doc_ocr.pipeline.runner import DemoPipelineRunner

runner = DemoPipelineRunner(ocr_backend="paddleocr")
result = runner.run("train_ticket", Path("examples/assets/paddle_sample_doc_00006737.jpg"))
print(result["ocr"]["text"])
```

## Current limits / TODO

- no pinned production dependency matrix yet for PaddleOCR + Paddle runtime
- no model asset management or cache control layer yet
- no GPU / batch / multi-process tuning yet
- no PaddleOCR-VL real inference path yet
- no document-specific post-processing tuned against PaddleOCR line segmentation yet

This is intentional: the goal of this pass is to replace the placeholder with a real backbone integration seam, without forcing CI or every contributor machine to install a heavy OCR stack.
