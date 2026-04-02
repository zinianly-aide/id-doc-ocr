import json
from pathlib import Path

from id_doc_ocr.plugins.medical_record.parser import parse_medical_record_fields


def test_parse_medical_record_fields_from_labeled_lines():
    fixture = json.loads(Path("examples/fixtures/medical_record/basic_outpatient_note.expected.json").read_text())
    fields = parse_medical_record_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected

    assert fields["sick_note_check"]["is_sick_note_like"] is False
    assert "病休/病假标题" in fields["sick_note_check"]["missing_features"]


def test_parse_medical_record_fields_detects_sick_note_like_fixture():
    fixture = json.loads(Path("examples/fixtures/medical_record/sick_note_like.expected.json").read_text())
    fields = parse_medical_record_fields(fixture["ocr_result"])

    assert fields["hospital_name"] == fixture["expected_fields"]["hospital_name"]
    assert fields["patient_name"] == fixture["expected_fields"]["patient_name"]
    assert fields["visit_date"] == fixture["expected_fields"]["visit_date"]
    assert fields["diagnosis"] == fixture["expected_fields"]["diagnosis"]
    assert fields["sick_note_check"]["is_sick_note_like"] is True
    assert fields["sick_note_check"]["confidence"] == "high"
    assert "病休/病假标题" in fields["sick_note_check"]["matched_features"]
    assert "病休/休息建议" in fields["sick_note_check"]["matched_features"]
