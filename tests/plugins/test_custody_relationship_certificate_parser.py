import json
from pathlib import Path

from id_doc_ocr.plugins.custody_relationship_certificate.parser import parse_custody_relationship_certificate_fields
from id_doc_ocr.plugins.custody_relationship_certificate.validator import validate_custody_relationship_certificate


def test_parse_custody_relationship_certificate_from_fixture():
    fixture = json.loads(
        Path("examples/fixtures/custody_relationship_certificate/shanghai_guardianship_text.expected.json").read_text()
    )
    fields = parse_custody_relationship_certificate_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected


def test_parse_custody_relationship_certificate_from_standalone_labels():
    ocr_result = {
        "lines": [
            {"text": "监护关系证明"},
            {"text": "未成年人姓名"},
            {"text": "周小禾"},
            {"text": "出生日期：2017年8月9日"},
            {"text": "法定监护人：周敏"},
            {"text": "关系：母女"},
            {"text": "现居住地址：上海市闵行区莘庄镇春申路66号"},
            {"text": "用途：用于学校报名"},
            {"text": "出具单位：上海市闵行区莘庄镇春申居民委员会"},
            {"text": "出具日期：2026年3月21日"},
        ]
    }

    fields = parse_custody_relationship_certificate_fields(ocr_result)

    assert fields["certificate_title"] == "监护关系证明"
    assert fields["child_name"] == "周小禾"
    assert fields["guardian_name"] == "周敏"
    assert fields["relation"] == "母女关系"
    assert fields["child_birth_date"] == "2017-08-09"
    assert fields["purpose"] == "用于学校报名"
    assert fields["issuing_authority"] == "上海市闵行区莘庄镇春申居民委员会"
    assert fields["issue_date"] == "2026-03-21"
    assert fields["authority_features"] == ["residents_committee"]


def test_validate_custody_relationship_certificate_warning_only():
    report = validate_custody_relationship_certificate(
        {
            "certificate_title": "抚养关系证明",
            "child_name": "安小宁",
            "guardian_name": "张敏",
            "relation": "抚养关系",
            "relation_statement": "安小宁现由张敏负责实际抚养。",
            "issuing_authority": "上海市浦东新区花木街道办事处",
            "authority_features": ["subdistrict_office"],
        }
    )

    assert report.accepted is True
    assert {issue.code for issue in report.issues} == {"missing_issue_date"}
    assert report.score == 0.85
