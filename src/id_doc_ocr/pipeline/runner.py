from __future__ import annotations

from id_doc_ocr.backbones.mock import MockGOTOCRAdapter, MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.core.registry import registry


class DemoPipelineRunner:
    def __init__(self) -> None:
        self.ocr = MockPaddleOCRAdapter()
        self.vlm = MockPaddleOCRVLAdapter()
        self.region_ocr = MockGOTOCRAdapter()

    def run(self, plugin_name: str, image: bytes, fields: dict | None = None) -> dict:
        plugin = registry.get(plugin_name)
        fields = fields or {}
        return {
            "plugin": plugin.metadata.name,
            "schema": plugin.get_schema_name(),
            "ocr": self.ocr.infer(image),
            "vlm": self.vlm.infer(image),
            "region_ocr": self.region_ocr.infer(image),
            "validation": plugin.validate_fields(fields),
        }
