from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from id_doc_ocr import plugins as _plugins  # noqa: F401
from id_doc_ocr.backbones.mock import MockGOTOCRAdapter, MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter
from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.core.registry import registry
from id_doc_ocr.datasets.schema import FieldAnnotation, InternalAnnotation, RegionAnnotation
from id_doc_ocr.detector.mock import MockDocumentDetectorAdapter
from id_doc_ocr.rectify.mock import MockRectifyPipeline
from id_doc_ocr.review import ReviewDecision, ReviewEvidence, ReviewEvidenceItem, ReviewReadyPayload, ReviewWarning
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

    def run(
        self,
        plugin_name: str,
        image: bytes | str | Path,
        fields: dict | None = None,
        sample_id: str | None = None,
        source_name: str | None = None,
        source_kind: str | None = None,
    ) -> dict[str, Any]:
        plugin = registry.get(plugin_name)
        resolved_sample_id = sample_id or self._resolve_sample_id(image)
        resolved_source_name = source_name or (str(image) if isinstance(image, (str, Path)) else None)
        resolved_source_kind = source_kind or ("path" if isinstance(image, (str, Path)) else "in_memory")
        provided_fields = fields or {}
        detector_result = self.detector.detect(image, preferred_doc_type=plugin_name)
        rectify_result = self.rectify.process(image, detection=detector_result.primary)
        rectified_image = rectify_result.image
        ocr_result = self.ocr.infer(rectified_image)
        parsed_fields = self.parse_plugin_fields(plugin, ocr_result)
        merged_fields = {**parsed_fields, **provided_fields}
        vlm_result = self.vlm.infer(rectified_image)
        vlm_backend_name = getattr(self.vlm, "info", None).name if getattr(self.vlm, "info", None) else self.vlm_backend
        annotation = self.to_internal_annotation(plugin_name, image, ocr_result, sample_id=resolved_sample_id)
        validation = plugin.validate_fields(merged_fields)
        review_ready = self.build_review_ready_payload(
            parsed_fields=parsed_fields,
            merged_fields=merged_fields,
            annotation=annotation,
            validation=validation,
            quality_summary=rectify_result.quality_summary.model_dump(),
        )
        rectify_payload = rectify_result.model_dump(exclude={"image"})
        rectify_payload["image"] = {
            "kind": "bytes" if isinstance(rectified_image, (bytes, bytearray)) else "path",
            "num_bytes": len(rectified_image) if isinstance(rectified_image, (bytes, bytearray)) else None,
            "preview": None if isinstance(rectified_image, (bytes, bytearray)) else str(rectified_image),
        }

        result = {
            "sample_id": resolved_sample_id,
            "plugin": plugin.metadata.name,
            "schema": plugin.get_schema_name(),
            "ocr_backend": self.ocr_backend,
            "vlm_backend": vlm_backend_name,
            "detector": detector_result.model_dump(),
            "rectify": rectify_payload,
            "quality": {
                "summary": rectify_result.quality_summary.model_dump(),
                "flags": [flag.model_dump() for flag in rectify_result.quality_summary.flags],
                "routing": {
                    "hint": rectify_result.quality_summary.routing_hint,
                    "review_recommended": rectify_result.quality_summary.review_recommended,
                },
            },
            "ocr": ocr_result,
            "parsed_fields": parsed_fields,
            "merged_fields": merged_fields,
            "vlm": vlm_result,
            "region_ocr": self.region_ocr.infer(b"" if not isinstance(rectified_image, (bytes, bytearray)) else rectified_image),
            "annotation": annotation,
            "validation": validation,
            "warnings": [warning.model_dump() for warning in review_ready.warnings],
            "decision": review_ready.decision.model_dump(),
            "evidence": review_ready.evidence.model_dump(),
            "review": review_ready.model_dump(),
        }
        if self.failure_dir and not result["validation"].get("accepted", False):
            write_failure_case(
                self.failure_dir,
                result,
                resolved_sample_id,
                metadata={
                    "sample_id": resolved_sample_id,
                    "plugin": plugin.metadata.name,
                    "ocr_backend": self.ocr_backend,
                    "vlm_backend": vlm_backend_name,
                    "source_kind": resolved_source_kind,
                    "source_name": resolved_source_name,
                },
            )
        return result

    def parse_plugin_fields(self, plugin: Any, ocr_result: dict[str, Any]) -> dict[str, Any]:
        parse_fn = getattr(plugin, "parse_fields", None)
        if callable(parse_fn):
            return parse_fn(ocr_result)
        return {}

    def _resolve_sample_id(self, image: bytes | str | Path) -> str:
        return Path(str(image)).stem if isinstance(image, (str, Path)) else "in_memory_sample"

    def to_internal_annotation(
        self,
        plugin_name: str,
        image: bytes | str | Path,
        ocr_result: dict[str, Any],
        sample_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_sample_id = sample_id or self._resolve_sample_id(image)
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
        annotation = InternalAnnotation(sample_id=resolved_sample_id, doc_type=plugin_name, regions=regions, fields=fields)
        return annotation.model_dump()

    def build_review_ready_payload(
        self,
        *,
        parsed_fields: dict[str, Any],
        merged_fields: dict[str, Any],
        annotation: dict[str, Any],
        validation: dict[str, Any],
        quality_summary: dict[str, Any],
    ) -> ReviewReadyPayload:
        warnings = self._build_review_warnings(validation=validation, quality_summary=quality_summary)
        decision = self._build_review_decision(validation=validation, quality_summary=quality_summary, warnings=warnings)
        evidence = self._build_review_evidence(
            parsed_fields=parsed_fields,
            merged_fields=merged_fields,
            annotation=annotation,
            validation=validation,
            quality_summary=quality_summary,
        )
        return ReviewReadyPayload(decision=decision, warnings=warnings, evidence=evidence)

    def _build_review_warnings(
        self,
        *,
        validation: dict[str, Any],
        quality_summary: dict[str, Any],
    ) -> list[ReviewWarning]:
        warnings: list[ReviewWarning] = []
        for flag in quality_summary.get("flags", []):
            warnings.append(
                ReviewWarning(
                    code=str(flag.get("code") or "quality_flag"),
                    severity=str(flag.get("severity") or "warning"),
                    message=str(flag.get("message") or flag.get("code") or "quality flag"),
                    source=str(flag.get("source") or "quality"),
                    stage="quality",
                    metric=flag.get("metric"),
                    value=flag.get("value"),
                    threshold=flag.get("threshold"),
                )
            )
        for issue in validation.get("issues", []):
            warnings.append(
                ReviewWarning(
                    code=str(issue.get("code") or "validation_issue"),
                    severity=str(issue.get("severity") or "warning"),
                    message=str(issue.get("message") or issue.get("code") or "validation issue"),
                    source="validation",
                    stage="validation",
                    field_name=issue.get("field_name"),
                )
            )
        return warnings

    def _build_review_decision(
        self,
        *,
        validation: dict[str, Any],
        quality_summary: dict[str, Any],
        warnings: list[ReviewWarning],
    ) -> ReviewDecision:
        validation_accepted = bool(validation.get("accepted", False))
        quality_passed = bool(quality_summary.get("passed", True))
        routing_hint = quality_summary.get("routing_hint")
        has_error = any(warning.severity == "error" for warning in warnings)
        has_warning = any(warning.severity == "warning" for warning in warnings)
        action = "accept"
        if routing_hint == "reject":
            action = "reject"
        elif not validation_accepted or has_error or quality_summary.get("review_recommended"):
            action = "review"
        elif has_warning:
            action = "accept_with_warning"
        return ReviewDecision(
            action=action,
            reason_codes=[warning.code for warning in warnings],
            review_recommended=action in {"review", "reject"},
            auto_accepted=action in {"accept", "accept_with_warning"},
            quality_passed=quality_passed,
            validation_accepted=validation_accepted,
            risk_score=float(quality_summary.get("risk_score") or 0.0),
        )

    def _build_review_evidence(
        self,
        *,
        parsed_fields: dict[str, Any],
        merged_fields: dict[str, Any],
        annotation: dict[str, Any],
        validation: dict[str, Any],
        quality_summary: dict[str, Any],
    ) -> ReviewEvidence:
        regions = annotation.get("regions", [])
        ocr_lines = [
            {
                "region_id": region.get("region_id"),
                "text": region.get("text"),
                "bbox": region.get("bbox"),
                "confidence": (region.get("attributes") or {}).get("score"),
            }
            for region in regions
        ]
        fields: list[ReviewEvidenceItem] = []
        for field_name, value in merged_fields.items():
            matched_region = self._match_region_for_field(value, regions)
            field_source = "parsed_field" if field_name in parsed_fields else "provided_field"
            fields.append(
                ReviewEvidenceItem(
                    field_name=field_name,
                    value=value,
                    source=field_source,
                    confidence=(matched_region.get("attributes") or {}).get("score") if matched_region else None,
                    bbox=matched_region.get("bbox") if matched_region else None,
                    region_id=matched_region.get("region_id") if matched_region else None,
                    text=matched_region.get("text") if matched_region else None,
                    matched=matched_region is not None,
                )
            )
        return ReviewEvidence(
            ocr_lines=ocr_lines,
            fields=fields,
            validator_issues=validation.get("issues", []),
            quality_flags=quality_summary.get("flags", []),
            summary={
                "ocr_line_count": len(ocr_lines),
                "field_count": len(fields),
                "matched_field_count": sum(1 for field in fields if field.matched),
                "validator_issue_count": len(validation.get("issues", [])),
                "quality_flag_count": len(quality_summary.get("flags", [])),
            },
        )

    def _match_region_for_field(self, value: Any, regions: list[dict[str, Any]]) -> dict[str, Any] | None:
        normalized_value = self._normalize_match_text(value)
        if not normalized_value:
            return None
        for region in regions:
            region_text = self._normalize_match_text(region.get("text"))
            if region_text and (normalized_value in region_text or region_text in normalized_value):
                return region
        return None

    def _normalize_match_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, BaseModel):
            value = value.model_dump()
        if isinstance(value, dict):
            return " ".join(self._normalize_match_text(v) for v in value.values()).strip()
        if isinstance(value, (list, tuple, set)):
            return " ".join(self._normalize_match_text(v) for v in value).strip()
        return str(value).strip().lower()
