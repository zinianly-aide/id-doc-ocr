from __future__ import annotations

from pathlib import Path

from id_doc_ocr.backbones.base import OCRBackboneAdapter
from id_doc_ocr.rectify.contracts import OrientationDecision, PerspectiveTransform, RectifyArtifact, RectifyResult
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
        artifacts = [
            RectifyArtifact(stage="perspective", payload=perspective.model_dump()),
            RectifyArtifact(stage="orientation", payload=orientation.model_dump()),
            RectifyArtifact(stage="quality", payload=quality.model_dump()),
        ]
        return RectifyResult(
            image=oriented_image,
            perspective=perspective,
            orientation=orientation,
            quality=quality,
            artifacts=artifacts,
            meta={
                "input_kind": type(normalized).__name__,
                "detection_doc_type": detection.doc_type if detection else None,
            },
        )
