from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import BackendSelectionError, DemoPipelineRunner


@dataclass(slots=True)
class InferenceServiceSettings:
    default_ocr_backend: str = "mock"
    default_vlm_backend: str = "mock"
    default_detector_backend: str = "mock"
    default_rectify_backend: str = "mock"
    default_field_parser_backend: str = "plugin"
    default_failure_dir: str | None = None


class InferenceService:
    """Small reusable inference facade for API and sidecar workers."""

    def __init__(self, settings: InferenceServiceSettings | Any | None = None) -> None:
        self.settings = settings or InferenceServiceSettings()

    def run(
        self,
        *,
        plugin_name: str,
        image: bytes,
        filename: str | None = None,
        fields: dict[str, Any] | None = None,
        ocr_backend: str | None = None,
        vlm_backend: str | None = None,
        detector_backend: str | None = None,
        rectify_backend: str | None = None,
        field_parser_backend: str | None = None,
        failure_dir: str | None = None,
    ) -> dict[str, Any]:
        if not plugin_name:
            raise ValueError("plugin_name is required")
        if plugin_name not in registry.list_plugins():
            raise ValueError(f"Unknown plugin: {plugin_name}")
        if not image:
            raise ValueError("image is empty")

        effective_ocr_backend = ocr_backend or getattr(self.settings, "default_ocr_backend", "mock")
        effective_vlm_backend = vlm_backend or getattr(self.settings, "default_vlm_backend", "mock")
        effective_detector_backend = detector_backend or getattr(self.settings, "default_detector_backend", "mock")
        effective_rectify_backend = rectify_backend or getattr(self.settings, "default_rectify_backend", "mock")
        effective_field_parser_backend = field_parser_backend or getattr(
            self.settings, "default_field_parser_backend", "plugin"
        )
        effective_failure_dir = failure_dir or getattr(self.settings, "default_failure_dir", None)

        DemoPipelineRunner.validate_backend_selection(
            ocr_backend=effective_ocr_backend,
            vlm_backend=effective_vlm_backend,
            detector_backend=effective_detector_backend,
            rectify_backend=effective_rectify_backend,
            field_parser_backend=effective_field_parser_backend,
        )
        runner = DemoPipelineRunner(
            ocr_backend=effective_ocr_backend,
            vlm_backend=effective_vlm_backend,
            detector_backend=effective_detector_backend,
            rectify_backend=effective_rectify_backend,
            field_parser_backend=effective_field_parser_backend,
            failure_dir=effective_failure_dir,
        )
        return runner.run(
            plugin_name=plugin_name,
            image=image,
            fields=fields or {},
            sample_id=(filename.rsplit(".", 1)[0] if filename else "leave_audit_attachment"),
            source_name=filename,
            source_kind="leave_audit_attachment",
        )
