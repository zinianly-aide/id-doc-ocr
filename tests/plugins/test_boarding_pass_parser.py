from id_doc_ocr.plugins.boarding_pass.parser import parse_boarding_pass_fields
from id_doc_ocr.plugins.boarding_pass.validator import validate_boarding_pass


def test_parse_boarding_pass_fields_from_known_lines():
    ocr_result = {
        "lines": [
            {"text": "BOARDING PASS"},
            {"text": "03DEC"},
            {"text": "MU 2379"},
            {"text": "TAIYUAN"},
            {"text": "FUZHOU"},
            {"text": "ZHANGQIWEI"},
            {"text": "ETKT 7813699238489/1"},
            {"text": "G11"},
        ]
    }
    fields = parse_boarding_pass_fields(ocr_result)
    assert fields["document_variant"] == "boarding_pass"
    assert fields["flight_number"] == "MU2379"
    assert fields["ticket_number"] == "7813699238489/1"
    assert fields["departure_airport"] == "TAIYUAN"
    assert fields["arrival_airport"] == "FUZHOU"
    assert fields["passenger_name"] == "ZHANGQIWEI"


def test_validate_boarding_pass_conflict():
    report = validate_boarding_pass(
        {
            "flight_number": "MU2379",
            "ticket_number": "7813699238489/1",
            "departure_date": "03DEC",
            "departure_airport": "TAIYUAN",
            "arrival_airport": "TAIYUAN",
        }
    )
    assert report.accepted is False
