from __future__ import annotations

from pathlib import Path

from id_doc_ocr.rectify.base import BaseRectifyPipeline, OrientationCorrector, PerspectiveCorrector, QualityScorer
from id_doc_ocr.rectify.contracts import OrientationDecision, PerspectiveTransform
from id_doc_ocr.schemas.types import Point, QualityReport


class MockPerspectiveCorrector(PerspectiveCorrector):
    def correct(self, image: bytes | str | Path) -> tuple[bytes | str, PerspectiveTransform]:
        transform = PerspectiveTransform(
            source_corners=[
                Point(x=0, y=0),
                Point(x=1, y=0),
                Point(x=1, y=1),
                Point(x=0, y=1),
            ],
            target_corners=[
                Point(x=0, y=0),
                Point(x=1, y=0),
                Point(x=1, y=1),
                Point(x=0, y=1),
            ],
            applied=False,
            confidence=0.5,
            method="mock_passthrough",
        )
        return image, transform


class MockOrientationCorrector(OrientationCorrector):
    def correct(self, image: bytes | str | Path) -> tuple[bytes | str, OrientationDecision]:
        decision = OrientationDecision(angle=0, applied=False, confidence=0.9, method="mock_passthrough")
        return image, decision


class MockQualityScorer(QualityScorer):
    def score(self, image: bytes | str | Path) -> QualityReport:
        return QualityReport(
            blur_score=0.95,
            glare_score=0.95,
            occlusion_score=0.95,
            passed=True,
            reasons=[],
        )


class MockRectifyPipeline(BaseRectifyPipeline):
    def __init__(self) -> None:
        super().__init__(
            perspective_corrector=MockPerspectiveCorrector(),
            orientation_corrector=MockOrientationCorrector(),
            quality_scorer=MockQualityScorer(),
        )
