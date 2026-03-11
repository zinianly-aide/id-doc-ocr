from __future__ import annotations

from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter


class PaddleOCRVLAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="paddleocr_vl", kind="vlm", description="PaddleOCR-VL adapter placeholder")

    def __init__(self, model_name: str = "PaddleOCR-VL-0.9B") -> None:
        self.model_name = model_name

    def infer(self, image: bytes) -> dict:
        return {
            "engine": self.info.name,
            "model_name": self.model_name,
            "status": "placeholder",
            "message": "Integrate real PaddleOCR-VL inference here.",
        }
