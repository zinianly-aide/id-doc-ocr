from __future__ import annotations

from pathlib import Path
from typing import Any

from id_doc_ocr import plugins as _plugins  # noqa: F401
from id_doc_ocr.backbones.mock import MockGOTOCRAdapter, MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter
from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.core.registry import registry
from id_doc_ocr.datasets.schema import FieldAnnotation, InternalAnnotation, RegionAnnotation
from id_doc_ocr.detector.mock import MockDocumentDetectorAdapter
from id_doc_ocr.rectify.mock import MockRectifyPipeline
from id_doc_ocr.tools.failure_log import write_failure_case


class DemoPipelineRunner:
    def __init__(
        self,
        ocr_backend: str = "mock",
        vlm_backend: str = "auto",
        failure_dir: str | None = None,
    ) -> None:
        self.ocr_backend = ocr_backend
        self.vlm_backend = vlm_backend
        self.failure_dir = failure_dir
        self.ocr = self._build_ocr_backend(ocr_backend)
        self.vlm = self._build_vlm_backend(vlm_backend)
        self.detector = MockDocumentDetectorAdapter()
        self.region_ocr = MockGOTOCRAdapter()
        self.rectify = MockRectifyPipeline()

    def _build_ocr_backend(self, ocr_backend: str) -> Any:
        if ocr_backend == "rapidocr":
            from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter

            return RapidOCRAdapter()
        if ocr_backend == "paddleocr":
            from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter

            return PaddleOCRAdapter()
        return MockPaddleOCRAdapter()

    def _build_vlm_backend(self, vlm_backend: str) -> Any:
        if vlm_backend == "mock":
            return MockPaddleOCRVLAdapter()
        if vlm_backend in {"paddleocr_vl", "auto"}:
            adapter = PaddleOCRVLAdapter(auto_init=vlm_backend != "mock")
            if vlm_backend == "paddleocr_vl":
                return adapter
            if adapter.is_runtime_available():
                return adapter
        return MockPaddleOCRVLAdapter()

    def run(self, plugin_name: str, image: bytes | str | Path, fields: dict | None = None) -> dict[str, Any]:
        plugin = registry.get(plugin_name)
        provided_fields = fields or {}
        detector_result = self.detector.detect(image, preferred_doc_type=plugin_name)
        rectify_result = self.rectify.process(image, detection=detector_result.primary)
        rectified_image = rectify_result.image
        ocr_result = self.ocr.infer(rectified_image)
        parsed_fields = self.parse_plugin_fields(plugin, ocr_result)
        merged_fields = {**parsed_fields, **provided_fields}
        vlm_result = self.vlm.infer(rectified_image)
        result = {
            "plugin": plugin.metadata.name,
            "schema": plugin.get_schema_name(),
            "ocr_backend": self.ocr_backend,
            "vlm_backend": getattr(self.vlm, "info", None).name if getattr(self.vlm, "info", None) else self.vlm_backend,
            "detector": detector_result.model_dump(),
            "rectify": rectify_result.model_dump(),
            "ocr": ocr_result,
            "parsed_fields": parsed_fields,
            "merged_fields": merged_fields,
            "vlm": vlm_result,
            "region_ocr": self.region_ocr.infer(b"" if not isinstance(rectified_image, (bytes, bytearray)) else rectified_image),
            "annotation": self.to_internal_annotation(plugin_name, image, ocr_result),
            "validation": plugin.validate_fields(merged_fields),
        }
        if self.failure_dir and not result["validation"].get("accepted", False):
            sample_id = Path(str(image)).stem if isinstance(image, (str, Path)) else "in_memory_sample"
            write_failure_case(self.failure_dir, result, sample_id)
        return result

    def parse_plugin_fields(self, plugin: Any, ocr_result: dict[str, Any]) -> dict[str, Any]:
        parse_fn = getattr(plugin, "parse_fields", None)
        if callable(parse_fn):
            return parse_fn(ocr_result)
        return {}

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
