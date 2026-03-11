from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


if __name__ == "__main__":
    sample = Path("examples/assets/paddle_sample_doc_00006737.jpg")
    runner = DemoPipelineRunner(ocr_backend="rapidocr")
    result = runner.run(
        plugin_name="train_ticket",
        image=sample,
        fields={
            "ticket_number": "demo",
            "train_number": "demo",
            "departure_station": "demo",
            "arrival_station": "demo",
            "departure_time": "demo",
        },
    )
    print("plugin:", result["plugin"])
    print("ocr_backend:", result["ocr_backend"])
    print("ocr_text_preview:")
    print(result["ocr"]["text"][:800])
    print("annotation_regions:", len(result["annotation"]["regions"]))
    print("annotation_fields:", len(result["annotation"]["fields"]))
