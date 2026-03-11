from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


if __name__ == "__main__":
    sample = Path("examples/assets/paddle_sample_doc_00006737.jpg")

    print("runtime:", PaddleOCRVLAdapter.runtime_status())

    runner = DemoPipelineRunner(ocr_backend="mock", vlm_backend="auto")
    result = runner.run(plugin_name="medical_record", image=sample)

    print("plugin:", result["plugin"])
    print("vlm_backend:", result["vlm_backend"])
    print("vlm_status:", result["vlm"].get("status", "mock"))
    print("vlm_text_preview:")
    print((result["vlm"].get("text") or str(result["vlm"]))[:800])
