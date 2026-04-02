from pathlib import Path

from id_doc_ocr.pipeline.runner import DemoPipelineRunner
from id_doc_ocr.rectify import BaseRectifyPipeline, MockRectifyPipeline, OrientationCorrector, PerspectiveCorrector, QualityScorer
from id_doc_ocr.rectify.contracts import OrientationDecision, PerspectiveTransform
from id_doc_ocr.schemas.types import BoundingBox, DocumentDetection, Point, QualityReport


def test_mock_rectify_pipeline_returns_contracts_for_bytes():
    pipeline = MockRectifyPipeline()

    result = pipeline.process(b"demo-image")

    assert result.image == b"demo-image"
    assert result.perspective.method == "mock_passthrough"
    assert result.orientation.angle == 0
    assert result.quality.passed is True
    assert result.quality_summary.routing_hint == "review"
    assert result.quality_summary.review_recommended is True
    assert any(flag.code == "weak_perspective_confidence" for flag in result.quality_summary.flags)
    assert [artifact.stage for artifact in result.artifacts] == ["perspective", "orientation", "quality", "quality_summary"]
    assert result.meta["input_kind"] == "bytes"


def test_mock_rectify_pipeline_normalizes_path_input():
    pipeline = MockRectifyPipeline()

    result = pipeline.process(Path("examples/assets/demo.jpg"))

    assert result.image == "examples/assets/demo.jpg"
    assert result.meta["input_kind"] == "str"


def test_runner_exposes_rectify_stage_output():
    runner = DemoPipelineRunner()

    result = runner.run("train_ticket", b"demo", fields={})

    assert "rectify" in result
    assert "quality" in result
    assert result["rectify"]["perspective"]["method"] == "mock_passthrough"
    assert result["rectify"]["orientation"]["angle"] == 0
    assert result["rectify"]["quality"]["passed"] is True
    assert result["rectify"]["quality_summary"]["routing_hint"] == "review"
    assert result["quality"]["routing"]["hint"] == "review"
    assert result["quality"]["summary"]["review_recommended"] is True
    assert any(flag["code"] == "weak_perspective_confidence" for flag in result["quality"]["flags"])


class StrongPerspectiveCorrector(PerspectiveCorrector):
    def correct(self, image):
        return image, PerspectiveTransform(
            source_corners=[Point(x=0, y=0), Point(x=10, y=0), Point(x=10, y=10), Point(x=0, y=10)],
            target_corners=[Point(x=0, y=0), Point(x=10, y=0), Point(x=10, y=10), Point(x=0, y=10)],
            applied=True,
            confidence=0.96,
            method="unit_test",
        )


class StrongOrientationCorrector(OrientationCorrector):
    def correct(self, image):
        return image, OrientationDecision(angle=0, applied=False, confidence=0.97, method="unit_test")


class FailingQualityScorer(QualityScorer):
    def score(self, image):
        return QualityReport(
            blur_score=0.42,
            glare_score=0.91,
            occlusion_score=0.38,
            passed=False,
            reasons=["blur_detected", "occlusion_detected"],
        )


class QualitySignalTestPipeline(BaseRectifyPipeline):
    def __init__(self) -> None:
        super().__init__(
            perspective_corrector=StrongPerspectiveCorrector(),
            orientation_corrector=StrongOrientationCorrector(),
            quality_scorer=FailingQualityScorer(),
        )


def test_rectify_quality_summary_promotes_risk_flags_for_review():
    pipeline = QualitySignalTestPipeline()
    detection = DocumentDetection(
        doc_type="train_ticket",
        bbox=BoundingBox(x1=0, y1=0, x2=100, y2=50),
        corners=[Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=50), Point(x=0, y=50)],
        confidence=0.93,
    )

    result = pipeline.process(b"demo-image", detection=detection)

    assert result.quality_summary.passed is False
    assert result.quality_summary.review_recommended is True
    assert result.quality_summary.routing_hint == "reject"
    assert result.quality_summary.risk_score > 0.5
    assert "blur_detected" in result.quality_summary.reasons
    assert "occlusion_detected" in result.quality_summary.reasons
    assert {flag.code for flag in result.quality_summary.flags} >= {
        "low_blur_score",
        "low_occlusion_score",
        "quality_gate_failed",
    }
