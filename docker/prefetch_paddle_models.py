from pathlib import Path

from id_doc_ocr.pipeline.runner import DemoPipelineRunner


runner = DemoPipelineRunner(
    ocr_backend="paddleocr",
    vlm_backend="mock",
    detector_backend="pil",
    rectify_backend="pil",
)
runner.run(
    plugin_name="boarding_pass",
    image=Path("examples/assets/paddle_sample_doc_00006737.jpg"),
)
print("prefetched paddle OCR runtime models")
