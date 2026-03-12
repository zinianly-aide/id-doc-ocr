from pathlib import Path

from id_doc_ocr.pipeline.runner import DemoPipelineRunner
from id_doc_ocr.rectify import MockRectifyPipeline


def test_mock_rectify_pipeline_returns_contracts_for_bytes():
    pipeline = MockRectifyPipeline()

    result = pipeline.process(b"demo-image")

    assert result.image == b"demo-image"
    assert result.perspective.method == "mock_passthrough"
    assert result.orientation.angle == 0
    assert result.quality.passed is True
    assert [artifact.stage for artifact in result.artifacts] == ["perspective", "orientation", "quality"]
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
    assert result["rectify"]["perspective"]["method"] == "mock_passthrough"
    assert result["rectify"]["orientation"]["angle"] == 0
    assert result["rectify"]["quality"]["passed"] is True
