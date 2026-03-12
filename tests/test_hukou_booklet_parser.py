from id_doc_ocr.plugins.hukou_booklet.parser import parse_hukou_booklet_fields


def test_parse_hukou_booklet_fields_from_labeled_lines():
    ocr_result = {
        "lines": [
            {"text": "常住人口登记卡"},
            {"text": "户号"},
            {"text": "123456789"},
            {"text": "户主姓名：张三"},
            {"text": "住址"},
            {"text": "北京市朝阳区幸福路100号"},
            {"text": "姓名：李四"},
            {"text": "与户主关系：之子"},
            {"text": "性别：男"},
            {"text": "公民身份号码"},
            {"text": "110105201001011234"},
        ]
    }

    fields = parse_hukou_booklet_fields(ocr_result)

    assert fields["doc_type"] == "hukou_booklet"
    assert fields["household_id"] == "123456789"
    assert fields["householder_name"] == "张三"
    assert fields["address"] == "北京市朝阳区幸福路100号"
    assert fields["member_name"] == "李四"
    assert fields["relation_to_head"] == "之子"
    assert fields["gender"] == "男"
    assert fields["id_number"] == "110105201001011234"
    assert fields["birth_date"] == "2010-01-01"


def test_parse_hukou_booklet_normalizes_inline_birth_date_and_gender():
    ocr_result = {
        "text": "\n".join(
            [
                "户号: 320101001234",
                "户主姓名: 王五",
                "姓名: 王小五",
                "与户主关系: 之女",
                "性别: Female",
                "出生日期: 2012年7月9日",
                "身份证号: 32010120120709122X",
            ]
        )
    }

    fields = parse_hukou_booklet_fields(ocr_result)

    assert fields["household_id"] == "320101001234"
    assert fields["gender"] == "女"
    assert fields["birth_date"] == "2012-07-09"
    assert fields["id_number"] == "32010120120709122X"
