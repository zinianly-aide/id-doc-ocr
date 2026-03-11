from id_doc_ocr.validator.china_id import validate_china_id_number


def test_invalid_china_id_number():
    issues = validate_china_id_number("110101199001011234")
    assert "checksum_invalid" in issues
