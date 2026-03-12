from pathlib import Path

from id_doc_ocr.detector import MockDocumentDetectorAdapter


def test_mock_detector_returns_quad_and_classification():
    adapter = MockDocumentDetectorAdapter()

    result = adapter.detect(Path("examples/assets/paddle_sample_doc_00006737.jpg"), preferred_doc_type="passport")

    assert result.doc_type == "passport"
    assert result.primary.confidence > 0.9
    assert len(result.quad.points) == 4
    assert result.classifications[0].label == "passport"
    assert result.raw["source"].endswith("paddle_sample_doc_00006737.jpg")


def test_mock_detector_without_hint_falls_back_to_generic_document():
    adapter = MockDocumentDetectorAdapter()

    result = adapter.detect(b"fake-image-bytes")

    assert result.doc_type == "unknown_document"
    assert [item.label for item in result.classifications] == ["unknown_document", "generic_document"]
