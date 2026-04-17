from io import BytesIO

import pytest

from id_doc_ocr.detector.pillow import PillowDocumentDetectorAdapter
from id_doc_ocr.rectify.pillow import PillowRectifyPipeline


pytest.importorskip("PIL")
from PIL import Image, ImageDraw  # noqa: E402


def _make_document_like_png_bytes() -> bytes:
    image = Image.new("RGB", (320, 200), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 25, 280, 175), fill=(235, 235, 235), outline="black", width=3)
    draw.text((70, 85), "DOC", fill="black")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_pillow_detector_localizes_document_bbox_from_bytes():
    adapter = PillowDocumentDetectorAdapter()

    result = adapter.detect(_make_document_like_png_bytes(), preferred_doc_type="passport")

    assert result.primary.doc_type == "passport"
    assert result.primary.confidence >= 0.55
    assert len(result.quad.points) == 4
    assert result.primary.bbox.x1 < result.primary.bbox.x2
    assert result.primary.bbox.y1 < result.primary.bbox.y2
    assert result.raw["strategy"] == "pillow_bbox"


def test_pillow_rectify_pipeline_returns_image_and_quality_summary():
    detector = PillowDocumentDetectorAdapter()
    detection = detector.detect(_make_document_like_png_bytes(), preferred_doc_type="passport").primary
    pipeline = PillowRectifyPipeline()

    result = pipeline.process(_make_document_like_png_bytes(), detection=detection)

    assert isinstance(result.image, (bytes, bytearray))
    assert result.perspective.method == "pil_quad_transform"
    assert result.quality_summary.metrics["quality_passed"] == result.quality.passed
    assert result.quality_summary.routing_hint in {"normal", "review", "reject"}
    assert len(result.artifacts) == 4
