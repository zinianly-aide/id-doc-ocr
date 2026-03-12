import json
from pathlib import Path

from id_doc_ocr.plugins.china_id.parser import parse_china_id_fields
from id_doc_ocr.plugins.china_id.plugin import plugin as china_id_plugin
from id_doc_ocr.validator.china_id import build_china_id_validation_report, validate_china_id_number


def test_parse_china_id_fields_from_front_fixture():
    fixture = json.loads(Path("examples/fixtures/china_id/basic_front.expected.json").read_text())
    fields = parse_china_id_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_validate_china_id_number_accepts_valid_number_and_lowercase_x():
    assert validate_china_id_number("110101199003074514") == []
    assert validate_china_id_number("11010119900101100x") == []


def test_invalid_china_id_number_reports_region_and_checksum_issues():
    issues = validate_china_id_number("000000199001011234")
    assert "region_code_invalid" in issues
    assert "checksum_invalid" in issues


def test_china_id_plugin_validate_fields_uses_report_shape():
    report = china_id_plugin.validate_fields({"id_number": "110101199003074514"})
    assert report["accepted"] is True
    assert report["issues"] == []


def test_build_china_id_validation_report_handles_missing_value():
    report = build_china_id_validation_report(None)
    assert report.accepted is False
    assert report.issues[0].code == "missing_id_number"
