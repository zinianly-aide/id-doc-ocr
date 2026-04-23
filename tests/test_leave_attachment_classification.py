from id_doc_ocr.classification.leave_attachment import classify_leave_attachment


def test_classify_leave_attachment_identifies_medical_certificate_keywords():
    result = classify_leave_attachment(
        {
            "lines": [
                {"text": "上海市第八人民医院"},
                {"text": "门诊诊断证明书"},
                {"text": "建议休息7天"},
            ]
        }
    )

    assert result["label"] == "MEDICAL_CERTIFICATE"
    assert result["confidence"] >= 0.8
    assert any("诊断证明" in keyword for keyword in result["matched_keywords"])


def test_classify_leave_attachment_identifies_birth_certificate_keywords():
    result = classify_leave_attachment("上海市出生医学证明\n新生儿姓名：安小宁\n母亲姓名：张敏")

    assert result["label"] == "BIRTH_CERTIFICATE"
    assert any("出生医学证明" in keyword for keyword in result["matched_keywords"])


def test_classify_leave_attachment_falls_back_to_unknown_without_signal():
    result = classify_leave_attachment({"lines": [{"text": "公司报销单"}, {"text": "金额：128.00"}]})

    assert result["label"] == "UNKNOWN"
    assert result["confidence"] == 0.0
    assert result["matched_keywords"] == []
