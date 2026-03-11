from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter


class MockPaddleOCRAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="paddleocr", kind="ocr", description="Mock PaddleOCR adapter")

    def infer(self, image: bytes) -> dict:
        return {"engine": self.info.name, "text": [], "fields": {}, "confidence": 0.9}


class MockPaddleOCRVLAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="paddleocr_vl", kind="vlm", description="Mock PaddleOCR-VL adapter")

    def infer(self, image: bytes) -> dict:
        return {"engine": self.info.name, "layout": [], "kv": {}, "confidence": 0.85}


class MockGOTOCRAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="got_ocr", kind="ocr", description="Mock GOT-OCR adapter")

    def infer(self, image: bytes) -> dict:
        return {"engine": self.info.name, "regions": [], "confidence": 0.8}
