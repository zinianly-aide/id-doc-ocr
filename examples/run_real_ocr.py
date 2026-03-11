from pathlib import Path

from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter


if __name__ == "__main__":
    adapter = RapidOCRAdapter()
    sample = Path("examples/assets/paddle_sample_doc_00006737.jpg")
    result = adapter.infer(sample)
    print("engine:", result["engine"])
    print("confidence:", result["confidence"])
    print("text preview:")
    print(result["text"][:1000])
