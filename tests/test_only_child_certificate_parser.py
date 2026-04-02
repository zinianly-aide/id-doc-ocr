import json
from pathlib import Path

from id_doc_ocr.plugins.only_child_certificate.parser import parse_only_child_certificate_fields


def test_parse_only_child_certificate_fields_from_labeled_lines():
    ocr_result = {
        "lines": [
            {"text": "独生子女父母光荣证"},
            {"text": "证号"},
            {"text": "沪A2024030168"},
            {"text": "子女姓名：安小宁"},
            {"text": "性别：男"},
            {"text": "出生日期"},
            {"text": "2020年06月18日"},
            {"text": "父亲姓名：李强"},
            {"text": "母亲姓名：张敏"},
            {"text": "发证机关：上海市浦东新区卫生健康委员会"},
            {"text": "发证日期：2024年03月20日"},
        ]
    }

    fields = parse_only_child_certificate_fields(ocr_result)

    assert fields["doc_type"] == "only_child_certificate"
    assert fields["certificate_title"] == "独生子女父母光荣证"
    assert fields["certificate_number"] == "沪A2024030168"
    assert fields["child_name"] == "安小宁"
    assert fields["child_gender"] == "男"
    assert fields["child_birth_date"] == "2020-06-18"
    assert fields["father_name"] == "李强"
    assert fields["mother_name"] == "张敏"
    assert fields["issuing_authority"] == "上海市浦东新区卫生健康委员会"
    assert fields["issue_date"] == "2024-03-20"


def test_parse_only_child_certificate_fields_from_fixture():
    fixture = json.loads(Path("examples/fixtures/only_child_certificate/shanghai_only_child_certificate_text.expected.json").read_text())

    fields = parse_only_child_certificate_fields(fixture["ocr_result"])

    for key, expected in fixture["expected_fields"].items():
        assert fields[key] == expected
