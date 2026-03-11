from __future__ import annotations

from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter


class GOTOCRAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="got_ocr", kind="ocr", description="GOT-OCR adapter placeholder")

    def __init__(self, model_name: str = "GOT-OCR-2.0") -> None:
        self.model_name = model_name

    def infer(self, image: bytes) -> dict:
        return {
            "engine": self.info.name,
            "model_name": self.model_name,
            "status": "placeholder",
            "message": "Integrate real GOT-OCR inference here.",
        }
