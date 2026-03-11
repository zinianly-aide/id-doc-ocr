from pathlib import Path

from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter


if __name__ == "__main__":
    sample = Path("examples/assets/paddle_sample_doc_00006737.jpg")
    adapter = PaddleOCRAdapter()
    result = adapter.infer(sample)
    print("engine:", result["engine"])
    print("confidence:", result["confidence"])
    print("config:", result["config"])
    print("text preview:")
    print(result["text"][:1000])
