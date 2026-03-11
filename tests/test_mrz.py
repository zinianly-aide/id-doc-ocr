from id_doc_ocr.parsers.mrz import parse_td3, validate_td3


def test_td3_parse_and_validate():
    lines = [
        "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
        "L898902C36UTO7408122F1204159ZE184226B<<<<<10",
    ]
    mrz = parse_td3(lines)
    assert mrz.issuing_country == "UTO"
    assert mrz.surname == "ERIKSSON"
    assert mrz.given_names == "ANNA MARIA"
    assert validate_td3(mrz) == []
