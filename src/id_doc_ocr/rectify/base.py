from __future__ import annotations

from pathlib import Path
from typing import Any

from id_doc_ocr.backbones.base import OCRBackboneAdapter
from id_doc_ocr.rectify.contracts import (
    OrientationDecision,
    PerspectiveTransform,
    QualityFlag,
    QualitySummary,
    RectifyArtifact,
    RectifyResult,
)
from id_doc_ocr.schemas.types import DocumentDetection, QualityReport


class PerspectiveCorrector:
    def correct(self, image: bytes | str | Path) -> tuple[bytes | str, PerspectiveTransform]:
        raise NotImplementedError


class OrientationCorrector:
    def correct(self, image: bytes | str | Path) -> tuple[bytes | str, OrientationDecision]:
        raise NotImplementedError


class QualityScorer:
    def score(self, image: bytes | str | Path) -> QualityReport:
        raise NotImplementedError


class RectifyPipelineStage:
    def process(self, image: bytes | str | Path, detection: DocumentDetection | None = None) -> RectifyResult:
        raise NotImplementedError


class BaseRectifyPipeline(RectifyPipelineStage):
    def __init__(
        self,
        perspective_corrector: PerspectiveCorrector,
        orientation_corrector: OrientationCorrector,
        quality_scorer: QualityScorer,
    ) -> None:
        self.perspective_corrector = perspective_corrector
        self.orientation_corrector = orientation_corrector
        self.quality_scorer = quality_scorer

    def process(self, image: bytes | str | Path, detection: DocumentDetection | None = None) -> RectifyResult:
        normalized = OCRBackboneAdapter.normalize_image_input(image)
        perspective_image, perspective = self.perspective_corrector.correct(normalized)
        oriented_image, orientation = self.orientation_corrector.correct(perspective_image)
        quality = self.quality_scorer.score(oriented_image)
        quality_summary = self._build_quality_summary(
            detection=detection,
            perspective=perspective,
            orientation=orientation,
            quality=quality,
        )
        artifacts = [
            RectifyArtifact(stage="perspective", payload=perspective.model_dump()),
            RectifyArtifact(stage="orientation", payload=orientation.model_dump()),
            RectifyArtifact(stage="quality", payload=quality.model_dump()),
            RectifyArtifact(stage="quality_summary", payload=quality_summary.model_dump()),
        ]
        return RectifyResult(
            image=oriented_image,
            perspective=perspective,
            orientation=orientation,
            quality=quality,
            quality_summary=quality_summary,
            artifacts=artifacts,
            meta={
                "input_kind": type(normalized).__name__,
                "detection_doc_type": detection.doc_type if detection else None,
            },
        )

    def _build_quality_summary(
        self,
        *,
        detection: DocumentDetection | None,
        perspective: PerspectiveTransform,
        orientation: OrientationDecision,
        quality: QualityReport,
    ) -> QualitySummary:
        flags: list[QualityFlag] = []
        reasons: list[str] = list(quality.reasons)
        metrics: dict[str, Any] = {
            "detector_confidence": detection.confidence if detection else None,
            "perspective_confidence": perspective.confidence,
            "perspective_applied": perspective.applied,
            "orientation_confidence": orientation.confidence,
            "orientation_angle": orientation.angle,
            "orientation_applied": orientation.applied,
            "blur_score": quality.blur_score,
            "glare_score": quality.glare_score,
            "occlusion_score": quality.occlusion_score,
            "quality_passed": quality.passed,
        }

        self._maybe_add_flag(
            flags,
            condition=detection is not None and detection.confidence < 0.8,
            code="low_detector_confidence",
            severity="warning",
            message="Detector confidence is low; document localization or routing may be unstable.",
            source="detector",
            metric="detector_confidence",
            value=detection.confidence if detection else None,
            threshold=0.8,
            reasons=reasons,
        )
        self._maybe_add_flag(
            flags,
            condition=perspective.confidence is not None and perspective.confidence < 0.7,
            code="weak_perspective_confidence",
            severity="warning",
            message="Perspective correction confidence is weak; warped crops may need review.",
            source="perspective",
            metric="perspective_confidence",
            value=perspective.confidence,
            threshold=0.7,
            reasons=reasons,
        )
        self._maybe_add_flag(
            flags,
            condition=orientation.confidence is not None and orientation.confidence < 0.85,
            code="low_orientation_confidence",
            severity="info",
            message="Orientation decision confidence is below the preferred operating range.",
            source="orientation",
            metric="orientation_confidence",
            value=orientation.confidence,
            threshold=0.85,
            reasons=reasons,
        )

        for metric_name, score in (
            ("blur_score", quality.blur_score),
            ("glare_score", quality.glare_score),
            ("occlusion_score", quality.occlusion_score),
        ):
            self._maybe_add_flag(
                flags,
                condition=score is not None and score < 0.85,
                code=f"low_{metric_name}",
                severity="warning",
                message=f"{metric_name} is below the preferred threshold.",
                source="quality",
                metric=metric_name,
                value=score,
                threshold=0.85,
                reasons=reasons,
            )

        if not quality.passed:
            self._maybe_add_flag(
                flags,
                condition=True,
                code="quality_gate_failed",
                severity="error",
                message="Rectified image failed the quality gate.",
                source="quality",
                metric="quality_passed",
                value=quality.passed,
                threshold=True,
                reasons=reasons,
            )

        risk_units = sum({"info": 0.5, "warning": 1.0, "error": 2.0}[flag.severity] for flag in flags)
        risk_score = min(1.0, round(risk_units / 4.0, 3))
        has_error = any(flag.severity == "error" for flag in flags)
        has_warning = any(flag.severity == "warning" for flag in flags)
        review_recommended = has_error or has_warning or not quality.passed
        routing_hint: str = "normal"
        if has_error or not quality.passed:
            routing_hint = "reject"
        elif review_recommended:
            routing_hint = "review"

        return QualitySummary(
            passed=quality.passed and not has_error,
            review_recommended=review_recommended,
            routing_hint=routing_hint,
            risk_score=risk_score,
            reasons=reasons,
            flags=flags,
            metrics=metrics,
        )

    def _maybe_add_flag(
        self,
        flags: list[QualityFlag],
        *,
        condition: bool,
        code: str,
        severity: str,
        message: str,
        source: str,
        metric: str | None,
        value: Any,
        threshold: Any,
        reasons: list[str],
    ) -> None:
        if not condition:
            return
        flags.append(
            QualityFlag(
                code=code,
                severity=severity,
                message=message,
                source=source,
                metric=metric,
                value=value,
                threshold=threshold,
            )
        )
        reasons.append(code)
