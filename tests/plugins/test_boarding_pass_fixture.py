import json
from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


def test_boarding_pass_public_fixture_matches_expected_fields():
    fixture = json.loads(Path("examples/fixtures/boarding_pass/public_sample_00006737.expected.json").read_text())
    runner = DemoPipelineRunner(ocr_backend="rapidocr")
    result = runner.run("boarding_pass", Path(fixture["sample"]))
    for key, expected in fixture["expected_fields"].items():
        assert result["parsed_fields"][key] == expected
