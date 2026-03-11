from __future__ import annotations

from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter


class PaddleOCRAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="paddleocr", kind="ocr", description="PaddleOCR adapter placeholder")

    def __init__(self, model_name: str = "PP-OCR") -> None:
        self.model_name = model_name

    def infer(self, image: bytes) -> dict:
        return {
            "engine": self.info.name,
            "model_name": self.model_name,
            "status": "placeholder",
            "message": "Integrate real PaddleOCR inference here.",
        }
