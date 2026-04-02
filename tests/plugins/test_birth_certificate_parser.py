import json
from pathlib import Path

from id_doc_ocr.plugins.birth_certificate.parser import parse_birth_certificate_fields
from id_doc_ocr.plugins.birth_certificate.validator import validate_birth_certificate


def test_parse_birth_certificate_fields_from_shanghai_fixture():
    fixture = json.loads(Path("examples/fixtures/birth_certificate/shanghai_basic_text_fixture.expected.json").read_text())
    fields = parse_birth_certificate_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_parse_birth_certificate_fields_from_standalone_labels():
    ocr_result = {
        "lines": [
            {"text": "出生医学证明"},
            {"text": "新生儿姓名"},
            {"text": "安小宁"},
            {"text": "性别：Male"},
            {"text": "出生日期"},
            {"text": "2024年3月16日"},
            {"text": "出生时间：8:06"},
            {"text": "孕周：38周"},
            {"text": "出生体重"},
            {"text": "3020克"},
            {"text": "出生地点：上海市浦东新区妇幼保健院"},
            {"text": "出生医学证明编号：T310000001"},
            {"text": "母亲姓名：张敏"},
            {"text": "母亲年龄：30岁"},
            {"text": "父亲姓名：李强"},
            {"text": "签发机构：上海市浦东新区妇幼保健院"},
            {"text": "签发日期：2024年3月20日"},
        ]
    }

    fields = parse_birth_certificate_fields(ocr_result)

    assert fields["child_name"] == "安小宁"
    assert fields["sex"] == "男"
    assert fields["date_of_birth"] == "2024-03-16"
    assert fields["time_of_birth"] == "08:06"
    assert fields["gestational_weeks"] == 38
    assert fields["birth_weight_grams"] == 3020
    assert fields["certificate_number"] == "T310000001"
    assert fields["issue_date"] == "2024-03-20"


def test_validate_birth_certificate_shanghai_warning_only():
    report = validate_birth_certificate(
        {
            "child_name": "安小宁",
            "sex": "男",
            "date_of_birth": "2024-03-16",
            "birth_place": "上海市第一妇婴保健院",
            "mother_name": "张敏",
            "certificate_number": "BAD-001",
        }
    )

    assert report.accepted is True
    assert {issue.code for issue in report.issues} == {"certificate_number_format_suspect"}
    assert report.score == 0.85
