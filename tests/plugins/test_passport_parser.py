import json
from pathlib import Path

from id_doc_ocr.plugins.passport.parser import extract_td3_mrz_lines, parse_passport_fields
from id_doc_ocr.plugins.passport.plugin import plugin
from id_doc_ocr.plugins.passport.validator import validate_passport


MRZ_LINE_1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
MRZ_LINE_2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"


def test_extract_td3_mrz_lines_normalizes_spaces():
    ocr_result = {
        "lines": [
            {"text": "Passport", "score": 0.99},
            {"text": "P<UTO ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<", "score": 0.98},
            {"text": "L898902C36 UTO7408122F1204159ZE184226B<<<<<10", "score": 0.97},
        ]
    }

    assert extract_td3_mrz_lines(ocr_result) == [MRZ_LINE_1, MRZ_LINE_2]


def test_parse_passport_fields_from_td3_mrz_lines():
    fields = parse_passport_fields({"lines": [{"text": MRZ_LINE_1}, {"text": MRZ_LINE_2}]})

    assert fields["document_variant"] == "passport"
    assert fields["mrz_lines"] == [MRZ_LINE_1, MRZ_LINE_2]
    assert fields["passport_number"] == "L898902C3"
    assert fields["surname"] == "ERIKSSON"
    assert fields["given_names"] == "ANNA MARIA"
    assert fields["birth_date"] == "1974-08-12"
    assert fields["expiry_date"] == "2012-04-15"
    assert fields["mrz_fields"]["nationality"] == "UTO"


def test_validate_passport_detects_cross_field_mismatch():
    parsed = parse_passport_fields({"lines": [{"text": MRZ_LINE_1}, {"text": MRZ_LINE_2}]})
    report = validate_passport({**parsed, "passport_number": "X898902C3"})

    assert report.accepted is False
    assert any(issue.code == "passport_number_mismatch" for issue in report.issues)


def test_parse_passport_fields_from_regression_fixture():
    fixture = json.loads(Path("examples/fixtures/passport/basic_td3_mrz.expected.json").read_text())
    fields = parse_passport_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_parse_passport_fields_from_text_fallback_fixture():
    fixture = json.loads(Path("examples/fixtures/passport/text_fallback_unspecified_sex.expected.json").read_text())
    fields = parse_passport_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected

    assert fields["mrz_lines"] == [
        MRZ_LINE_1,
        "L898902C36UTO7408122<1204159ZE184226B<<<<<10",
    ]
    assert fields["mrz_fields"]["sex"] is None


def test_passport_plugin_exposes_parser_and_validator():
    parsed = plugin.parse_fields({"lines": [{"text": MRZ_LINE_1}, {"text": MRZ_LINE_2}]})
    report = plugin.validate_fields(parsed)

    assert parsed["passport_number"] == "L898902C3"
    assert report["accepted"] is True
