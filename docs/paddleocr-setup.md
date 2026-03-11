# PaddleOCR setup

This repo now includes a concrete `PaddleOCRAdapter` integration layer, but it still treats PaddleOCR as an optional local runtime dependency.

## What is implemented

- lazy runtime import of `paddleocr`
- normalized adapter output: `engine`, `text`, `lines`, `confidence`
- environment-based config knobs for quick local experiments
- demo runner wiring via `DemoPipelineRunner(ocr_backend="paddleocr")`
- unit tests that validate normalization and runtime checks without requiring a heavyweight install in CI

## Local install options

Pick one of these approaches depending on how heavy you want the environment to be.

### Option A: project extras

```bash
pip install -e '.[dev,paddle]'
```

### Option B: manual install

```bash
pip install -e '.[dev]'
pip install paddleocr
```

Depending on your platform, you may also need the matching Paddle / PaddlePaddle runtime recommended by PaddleOCR.

## Environment knobs

- `ID_DOC_OCR_PADDLE_LANG` — default `ch`
- `ID_DOC_OCR_PADDLE_USE_ANGLE_CLS` — default `1`
- `ID_DOC_OCR_PADDLE_ENABLE_MKLDNN` — default `0`

Example:

```bash
export ID_DOC_OCR_PADDLE_LANG=en
export ID_DOC_OCR_PADDLE_USE_ANGLE_CLS=1
python examples/run_paddleocr_demo.py
```

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
