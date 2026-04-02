import json
from pathlib import Path

from id_doc_ocr.plugins.diagnosis_proof.parser import parse_diagnosis_proof_fields
from id_doc_ocr.plugins.diagnosis_proof.validator import validate_diagnosis_proof


def test_parse_diagnosis_proof_fields_from_text_fixture():
    fixture = json.loads(Path("examples/fixtures/diagnosis_proof/diagnosis_certificate_text.expected.json").read_text())
    fields = parse_diagnosis_proof_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_parse_diagnosis_proof_fields_from_minimal_fixture():
    fixture = json.loads(Path("examples/fixtures/diagnosis_proof/diagnosis_certificate_minimal.expected.json").read_text())
    fields = parse_diagnosis_proof_fields(fixture["ocr_result"])

    assert fields["hospital_name"] == fixture["expected_fields"]["hospital_name"]
    assert fields["certificate_title"] == fixture["expected_fields"]["certificate_title"]
    assert fields["diagnosis"] == fixture["expected_fields"]["diagnosis"]
    assert fields["advice"] == fixture["expected_fields"]["advice"]
    assert fields["rest_days"] == 3
    assert fields["seal_present"] is False


def test_validate_diagnosis_proof_warning_only_without_seal():
    report = validate_diagnosis_proof(
        {
            "hospital_name": "杭州市某医院",
            "certificate_title": "疾病诊断证明书",
            "diagnosis": ["急性上呼吸道感染"],
            "advice": ["建议门诊治疗并休息3天"],
            "issue_date": "2026-03-18",
            "physician_name": "王宁",
            "department": "呼吸内科",
            "seal_present": False,
        }
    )

    assert report.accepted is True
    assert any(issue.code == "missing_seal" for issue in report.issues)
    assert report.score == 0.85
