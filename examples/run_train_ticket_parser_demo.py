from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


if __name__ == "__main__":
    sample = Path("examples/assets/paddle_sample_doc_00006737.jpg")
    runner = DemoPipelineRunner(ocr_backend="rapidocr")
    result = runner.run(plugin_name="train_ticket", image=sample)
    print("parsed_fields:")
    for k, v in result["parsed_fields"].items():
        print(f"- {k}: {v}")
    print("validation:")
    print(result["validation"])
