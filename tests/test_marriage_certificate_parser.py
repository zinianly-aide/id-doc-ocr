import json
from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import DemoPipelineRunner
from id_doc_ocr.plugins.marriage_certificate.parser import parse_marriage_certificate_fields
from id_doc_ocr.plugins.marriage_certificate.validator import validate_marriage_certificate


FIXTURE_PATH = Path("examples/fixtures/marriage_certificate/basic_text_fixture.expected.json")


def test_parse_marriage_certificate_fields_from_text_fixture():
    fixture = json.loads(FIXTURE_PATH.read_text())
    fields = parse_marriage_certificate_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_validate_marriage_certificate_accepts_complete_fields():
    fixture = json.loads(FIXTURE_PATH.read_text())
    report = validate_marriage_certificate(fixture["expected_fields"])

    assert report.accepted is True
    assert report.score == 1.0
    assert report.issues == []


def test_runner_registers_and_executes_marriage_certificate_plugin():
    assert "marriage_certificate" in registry.list_plugins()

    runner = DemoPipelineRunner()
    result = runner.run("marriage_certificate", b"demo", fields={})

    assert result["plugin"] == "marriage_certificate"
    assert result["analysis"]["doc_type"] == "marriage_certificate"
