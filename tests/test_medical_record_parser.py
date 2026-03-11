import json
from pathlib import Path

from id_doc_ocr.plugins.medical_record.parser import parse_medical_record_fields


def test_parse_medical_record_fields_from_labeled_lines():
    fixture = json.loads(Path("examples/fixtures/medical_record/basic_outpatient_note.expected.json").read_text())
    fields = parse_medical_record_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected
