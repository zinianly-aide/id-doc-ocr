import json
from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import DemoPipelineRunner
from id_doc_ocr.plugins.marriage_certificate.parser import parse_marriage_certificate_fields
from id_doc_ocr.plugins.marriage_certificate.schema import MarriageCertificateDocument
from id_doc_ocr.plugins.marriage_certificate.validator import validate_marriage_certificate


FIXTURE_PATH = Path("examples/fixtures/marriage_certificate/basic_text_fixture.expected.json")
DATASET_EXPECTATION_PATHS = [
    Path("datasets/marriage/pass/synthetic_complete_match/expected.json"),
    Path("datasets/marriage/review/synthetic_holder_mismatch/expected.json"),
    Path("datasets/marriage/weak/synthetic_suspect_authority/expected.json"),
]


def test_parse_marriage_certificate_fields_from_text_fixture():
    fixture = json.loads(FIXTURE_PATH.read_text())
    fields = parse_marriage_certificate_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_marriage_certificate_schema_accepts_fixture_fields():
    fixture = json.loads(FIXTURE_PATH.read_text())

    document = MarriageCertificateDocument(**fixture["expected_fields"])

    assert document.doc_type == "marriage_certificate"
    assert document.holder_name == fixture["expected_fields"]["holder_name"]
    assert document.person_b_name == fixture["expected_fields"]["person_b_name"]



def test_validate_marriage_certificate_accepts_complete_fields():
    fixture = json.loads(FIXTURE_PATH.read_text())
    report = validate_marriage_certificate(fixture["expected_fields"])

    assert report.accepted is True
    assert report.score == 1.0
    assert report.issues == []



def test_validate_marriage_certificate_rejects_minimum_incomplete_fields():
    report = validate_marriage_certificate(
        {
            "doc_type": "marriage_certificate",
            "certificate_title": None,
            "holder_name": "张三",
            "person_a_name": "张三",
            "registration_date": None,
            "person_b_name": None,
            "registration_authority": None,
        }
    )

    assert report.accepted is False
    assert {issue.code for issue in report.issues} >= {
        "missing_certificate_title",
        "missing_registration_date",
        "missing_person_b_name",
        "missing_registration_authority",
    }



def test_validate_marriage_certificate_flags_holder_name_not_in_couple():
    report = validate_marriage_certificate(
        {
            "doc_type": "marriage_certificate",
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "王五",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        }
    )

    assert report.accepted is True
    assert any(issue.code == "holder_name_not_in_couple" for issue in report.issues)



def test_validate_marriage_certificate_flags_suspect_authority():
    report = validate_marriage_certificate(
        {
            "doc_type": "marriage_certificate",
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "某某办公室",
        }
    )

    assert report.accepted is True
    assert any(issue.code == "registration_authority_suspect" for issue in report.issues)



def test_validate_marriage_certificate_flags_suspect_title():
    report = validate_marriage_certificate(
        {
            "doc_type": "marriage_certificate",
            "certificate_title": "证明材料",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        }
    )

    assert report.accepted is True
    assert any(issue.code == "certificate_title_suspect" for issue in report.issues)



def test_marriage_dataset_expectation_skeleton_files_are_well_formed():
    for path in DATASET_EXPECTATION_PATHS:
        payload = json.loads(path.read_text())
        assert payload["leave_type"] == "MARRIAGE"
        assert payload["expected_status"] in {"PASS", "REVIEW"}
        assert isinstance(payload["expected_risks"], list)
        assert isinstance(payload["expected_warnings"], list)



def test_runner_registers_and_executes_marriage_certificate_plugin():
    assert "marriage_certificate" in registry.list_plugins()

    runner = DemoPipelineRunner()
    result = runner.run("marriage_certificate", b"demo", fields={})

    assert result["plugin"] == "marriage_certificate"
    assert result["analysis"]["doc_type"] == "marriage_certificate"
