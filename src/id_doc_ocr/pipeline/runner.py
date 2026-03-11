from __future__ import annotations

from pathlib import Path
from typing import Any

from id_doc_ocr.backbones.mock import MockGOTOCRAdapter, MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.core.registry import registry
from id_doc_ocr.datasets.schema import FieldAnnotation, InternalAnnotation, RegionAnnotation


class DemoPipelineRunner:
    def __init__(self, ocr_backend: str = "mock") -> None:
        self.ocr_backend = ocr_backend
        if ocr_backend == "rapidocr":
            from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter

            self.ocr = RapidOCRAdapter()
        else:
            self.ocr = MockPaddleOCRAdapter()
        self.vlm = MockPaddleOCRVLAdapter()
        self.region_ocr = MockGOTOCRAdapter()

    def run(self, plugin_name: str, image: bytes | str | Path, fields: dict | None = None) -> dict[str, Any]:
        plugin = registry.get(plugin_name)
        fields = fields or {}
        ocr_result = self.ocr.infer(image)
        return {
            "plugin": plugin.metadata.name,
            "schema": plugin.get_schema_name(),
            "ocr_backend": self.ocr_backend,
            "ocr": ocr_result,
            "vlm": self.vlm.infer(b"" if not isinstance(image, (bytes, bytearray)) else image),
            "region_ocr": self.region_ocr.infer(b"" if not isinstance(image, (bytes, bytearray)) else image),
            "annotation": self.to_internal_annotation(plugin_name, image, ocr_result),
            "validation": plugin.validate_fields(fields),
        }

    def to_internal_annotation(
        self, plugin_name: str, image: bytes | str | Path, ocr_result: dict[str, Any]
    ) -> dict[str, Any]:
        sample_id = Path(str(image)).stem if isinstance(image, (str, Path)) else "in_memory_sample"
        regions: list[RegionAnnotation] = []
        fields: list[FieldAnnotation] = []
        for idx, line in enumerate(ocr_result.get("lines", [])):
            box = line.get("box")
            flat_box = None
            if isinstance(box, list) and len(box) == 4:
                try:
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    flat_box = [min(xs), min(ys), max(xs), max(ys)]
                except Exception:
                    flat_box = None
            region_id = f"r{idx+1}"
            regions.append(
                RegionAnnotation(
                    region_id=region_id,
                    label="ocr_line",
                    bbox=flat_box,
                    text=line.get("text"),
                    attributes={"score": line.get("score")},
                )
            )
            fields.append(
                FieldAnnotation(
                    field_name=f"ocr_line_{idx+1}",
                    value=line.get("text"),
                    region_id=region_id,
                    confidence=line.get("score"),
                )
            )
        annotation = InternalAnnotation(sample_id=sample_id, doc_type=plugin_name, regions=regions, fields=fields)
        return annotation.model_dump()
