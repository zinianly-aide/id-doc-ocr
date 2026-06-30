from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from id_doc_ocr import plugins as _plugins  # noqa: F401
from id_doc_ocr.backbones.mock import MockGOTOCRAdapter, MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter
from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.classification.leave_attachment import classify_leave_attachment
from id_doc_ocr.core.registry import registry
from id_doc_ocr.datasets.schema import FieldAnnotation, InternalAnnotation, RegionAnnotation
from id_doc_ocr.detector.mock import MockDocumentDetectorAdapter
from id_doc_ocr.detector.pillow import PillowDocumentDetectorAdapter
from id_doc_ocr.parsers.dify_field_parser import DifyFieldParser
from id_doc_ocr.rectify.mock import MockRectifyPipeline
from id_doc_ocr.rectify.pillow import PillowRectifyPipeline
from id_doc_ocr.review import ReviewDecision, ReviewEvidence, ReviewEvidenceItem, ReviewReadyPayload, ReviewWarning
from id_doc_ocr.schemas.types import AnalysisRisk, DocumentAnalysisResult, ExtractedField
from id_doc_ocr.tools.failure_log import write_failure_case


class BackendSelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class StageBackendSpec:
    name: str
    builder: Callable[[], Any]
    availability_check: Callable[[], bool]
    unavailable_message: str | None = None
    display_name: str | None = None


PLUGIN_ATTACHMENT_LABELS = {
    "diagnosis_proof": "MEDICAL_CERTIFICATE",
    "medical_record": "MEDICAL_CERTIFICATE",
    "marriage_certificate": "MARRIAGE_CERTIFICATE",
    "birth_certificate": "BIRTH_CERTIFICATE",
    "train_ticket": "TRAIN_TICKET",
}


class DemoPipelineRunner:
    STAGE_LABELS = {
        "ocr": "OCR",
        "vlm": "VLM",
        "detector": "detector",
        "rectify": "rectify",
    }
    STAGE_BACKENDS: dict[str, dict[str, StageBackendSpec]] = {
        "ocr": {
            "mock": StageBackendSpec(
                name="mock",
                builder=lambda: MockPaddleOCRAdapter(),
                availability_check=lambda: True,
            ),
            "rapidocr": StageBackendSpec(
                name="rapidocr",
                builder=lambda: __import__("id_doc_ocr.backbones.rapidocr", fromlist=["RapidOCRAdapter"]).RapidOCRAdapter(),
                availability_check=lambda: __import__("id_doc_ocr.backbones.rapidocr", fromlist=["RapidOCRAdapter"]).RapidOCRAdapter.is_available(),
                unavailable_message="OCR backend 'rapidocr' is unavailable. Install rapidocr_onnxruntime to enable the ONNX baseline.",
            ),
            "paddleocr": StageBackendSpec(
                name="paddleocr",
                builder=lambda: PaddleOCRAdapter(),
                availability_check=lambda: PaddleOCRAdapter.is_available(),
                unavailable_message="OCR backend 'paddleocr' is unavailable. See docs/paddleocr-setup.md for local setup instructions.",
            ),
        },
        "vlm": {
            "mock": StageBackendSpec(
                name="mock",
                builder=lambda: MockPaddleOCRVLAdapter(),
                availability_check=lambda: True,
            ),
            "paddleocr_vl": StageBackendSpec(
                name="paddleocr_vl",
                builder=lambda: PaddleOCRVLAdapter(auto_init=True),
                availability_check=lambda: PaddleOCRVLAdapter.is_runtime_available(),
                unavailable_message="VLM backend 'paddleocr_vl' is unavailable. Install optional PaddleOCR-VL runtime dependencies first.",
            ),
            "auto": StageBackendSpec(
                name="auto",
                builder=lambda: PaddleOCRVLAdapter(auto_init=True),
                availability_check=lambda: PaddleOCRVLAdapter.is_runtime_available(),
                unavailable_message="VLM backend 'auto' is unavailable. Install optional PaddleOCR-VL runtime dependencies first.",
            ),
        },
        "detector": {
            "mock": StageBackendSpec(
                name="mock",
                builder=lambda: MockDocumentDetectorAdapter(),
                availability_check=lambda: True,
            ),
            "pil": StageBackendSpec(
                name="pil",
                builder=lambda: PillowDocumentDetectorAdapter(),
                availability_check=lambda: PillowDocumentDetectorAdapter.is_available(),
                unavailable_message="Detector backend 'pil' is unavailable. Install Pillow to enable image-aware document localization.",
            ),
        },
        "rectify": {
            "mock": StageBackendSpec(
                name="mock",
                builder=lambda: MockRectifyPipeline(),
                availability_check=lambda: True,
                display_name="MockRectifyPipeline",
            ),
            "pil": StageBackendSpec(
                name="pil",
                builder=lambda: PillowRectifyPipeline(),
                availability_check=lambda: PillowRectifyPipeline.is_available(),
                unavailable_message="Rectify backend 'pil' is unavailable. Install Pillow to enable image-aware rectify and quality scoring.",
                display_name="PillowRectifyPipeline",
            ),
        },
    }

    def __init__(
        self,
        ocr_backend: str = "mock",
        vlm_backend: str = "auto",
        detector_backend: str = "mock",
        rectify_backend: str = "mock",
        field_parser_backend: str = "plugin",
        failure_dir: str | None = None,
    ) -> None:
        if field_parser_backend not in {"plugin", "dify"}:
            raise BackendSelectionError(
                "Unknown field parser backend: "
                f"{field_parser_backend}. Supported values: dify, plugin"
            )
        self.backend_selection = {
            "ocr": ocr_backend,
            "vlm": vlm_backend,
            "detector": detector_backend,
            "rectify": rectify_backend,
            "field_parser": field_parser_backend,
        }
        self.ocr_backend = ocr_backend
        self.vlm_backend = vlm_backend
        self.detector_backend = detector_backend
        self.rectify_backend = rectify_backend
        self.field_parser_backend = field_parser_backend
        self.failure_dir = failure_dir
        self.ocr = self._build_stage_backend("ocr", ocr_backend)
        self.vlm = self._build_stage_backend("vlm", vlm_backend)
        self.detector = self._build_stage_backend("detector", detector_backend)
        self.region_ocr = MockGOTOCRAdapter()
        self.rectify = self._build_stage_backend("rectify", rectify_backend)
        self.field_parser = DifyFieldParser() if field_parser_backend == "dify" else None

    @classmethod
    def stage_backend_names(cls, stage: str) -> list[str]:
        return sorted(cls.STAGE_BACKENDS[stage])

    @classmethod
    def build_stage_inventory(cls, stages: list[str] | tuple[str, ...] | None = None) -> dict[str, list[dict[str, Any]]]:
        inventory: dict[str, list[dict[str, Any]]] = {}
        selected_stages = list(stages) if stages is not None else list(cls.STAGE_BACKENDS)
        for stage in selected_stages:
            stage_specs = cls.STAGE_BACKENDS[stage]
            inventory[stage] = []
            for backend_name in cls.stage_backend_names(stage):
                spec = stage_specs[backend_name]
                availability = {"available": bool(spec.availability_check())}
                info = None
                instance = None
                try:
                    if availability["available"]:
                        instance = spec.builder()
                        info = getattr(instance, "info", None)
                except Exception:
                    info = None
                inventory[stage].append(
                    {
                        "backend": backend_name,
                        "name": getattr(info, "name", None) or spec.display_name or (instance.__class__.__name__ if instance is not None else None) or backend_name,
                        "kind": getattr(info, "kind", None) or stage,
                        "description": getattr(info, "description", None) or "",
                        "version": getattr(info, "version", None),
                        "available": availability["available"],
                        "availability": availability,
                    }
                )
        return inventory

    @classmethod
    def validate_backend_selection(
        cls,
        *,
        ocr_backend: str,
        vlm_backend: str,
        detector_backend: str = "mock",
        rectify_backend: str = "mock",
        field_parser_backend: str = "plugin",
    ) -> None:
        selections = {
            "ocr": ocr_backend,
            "vlm": vlm_backend,
            "detector": detector_backend,
            "rectify": rectify_backend,
        }
        for stage, backend_name in selections.items():
            cls._validate_stage_backend(stage, backend_name)
        if field_parser_backend not in {"plugin", "dify"}:
            raise BackendSelectionError(
                "Unknown field parser backend: "
                f"{field_parser_backend}. Supported values: dify, plugin"
            )

    @classmethod
    def _validate_stage_backend(cls, stage: str, backend_name: str) -> None:
        stage_specs = cls.STAGE_BACKENDS[stage]
        stage_label = cls.STAGE_LABELS.get(stage, stage)
        if backend_name not in stage_specs:
            raise BackendSelectionError(
                f"Unknown {stage_label} backend: {backend_name}. Supported values: {', '.join(sorted(stage_specs))}"
            )
        spec = stage_specs[backend_name]
        if not spec.availability_check() and spec.unavailable_message:
            raise BackendSelectionError(spec.unavailable_message)

    def _build_stage_backend(self, stage: str, backend_name: str) -> Any:
        return self.STAGE_BACKENDS[stage][backend_name].builder()

    def run(
        self,
        plugin_name: str,
        image: bytes | str | Path,
        fields: dict | None = None,
        prompt_context: dict[str, Any] | None = None,
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
        parsed_fields = self.parse_fields(plugin, ocr_result, prompt_context=prompt_context)
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

        analysis = self.build_analysis_payload(
            plugin_name=plugin.metadata.name,
            detector_result=detector_result.model_dump(),
            merged_fields=merged_fields,
            review_ready=review_ready,
            validation=validation,
            ocr_backend=self.ocr_backend,
            vlm_backend=vlm_backend_name,
            field_parser_backend=self.field_parser_backend,
        )

        result = {
            "sample_id": resolved_sample_id,
            "plugin": plugin.metadata.name,
            "schema": plugin.get_schema_name(),
            "ocr_backend": self.ocr_backend,
            "vlm_backend": vlm_backend_name,
            "detector_backend": self.detector_backend,
            "rectify_backend": self.rectify_backend,
            "field_parser_backend": self.field_parser_backend,
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
            "analysis": analysis,
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
                    "detector_backend": self.detector_backend,
                    "rectify_backend": self.rectify_backend,
                    "field_parser_backend": self.field_parser_backend,
                    "source_kind": resolved_source_kind,
                    "source_name": resolved_source_name,
                },
            )
        return result

    def parse_fields(self, plugin: Any, ocr_result: dict[str, Any], prompt_context: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.field_parser_backend == "dify":
            if self.field_parser is None:
                self.field_parser = DifyFieldParser()
            return self.field_parser.parse(plugin=plugin, ocr_result=ocr_result, prompt_context=prompt_context)
        return self.parse_plugin_fields(plugin, ocr_result)

    def parse_plugin_fields(self, plugin: Any, ocr_result: dict[str, Any]) -> dict[str, Any]:
        parse_fn = getattr(plugin, "parse_fields", None)
        if callable(parse_fn):
            return parse_fn(ocr_result)
        return {}

    def build_analysis_payload(
        self,
        *,
        plugin_name: str,
        detector_result: dict[str, Any],
        merged_fields: dict[str, Any],
        review_ready: ReviewReadyPayload,
        validation: dict[str, Any],
        ocr_backend: str,
        vlm_backend: str,
        field_parser_backend: str,
    ) -> dict[str, Any]:
        detector_primary = detector_result.get("primary") or {}
        attachment_classification = classify_leave_attachment({"lines": review_ready.evidence.ocr_lines})
        if attachment_classification["label"] == "UNKNOWN" and plugin_name in PLUGIN_ATTACHMENT_LABELS:
            attachment_classification = {
                "label": PLUGIN_ATTACHMENT_LABELS[plugin_name],
                "confidence": max(float(attachment_classification.get("confidence") or 0.0), 0.51),
                "matched_keywords": attachment_classification.get("matched_keywords", []),
            }
        extracted_fields = [
            ExtractedField(
                name=field.field_name,
                value=field.value,
                confidence=field.confidence,
                source=field.source,
                bbox=field.bbox,
                evidence_text=field.text,
                matched=field.matched,
            )
            for field in review_ready.evidence.fields
        ]
        analysis = DocumentAnalysisResult(
            doc_type=plugin_name,
            doc_type_confidence=detector_primary.get("confidence"),
            classification_evidence={
                "plugin": plugin_name,
                "detector_doc_type": detector_primary.get("doc_type"),
                "ocr_backend": ocr_backend,
                "vlm_backend": vlm_backend,
                "field_parser_backend": field_parser_backend,
                "attachment_label": attachment_classification["label"],
                "attachment_confidence": attachment_classification["confidence"],
                "matched_keywords": attachment_classification["matched_keywords"],
            },
            extracted_fields=extracted_fields,
            validation=validation,
            review=review_ready.model_dump(),
            risk=AnalysisRisk(
                score=review_ready.decision.risk_score,
                review_action=review_ready.decision.action,
                review_recommended=review_ready.decision.review_recommended,
                quality_passed=review_ready.decision.quality_passed,
                validation_accepted=review_ready.decision.validation_accepted,
            ),
            raw_artifacts={
                "detector": detector_result,
                "ocr_line_count": len(review_ready.evidence.ocr_lines),
                "warning_count": len(review_ready.warnings),
                "merged_field_count": len(merged_fields),
                "field_parser_backend": field_parser_backend,
            },
        )
        return analysis.model_dump()

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
