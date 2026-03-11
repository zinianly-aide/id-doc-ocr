from id_doc_ocr.plugins.boarding_pass.parser import parse_boarding_pass_fields
from id_doc_ocr.plugins.boarding_pass.validator import validate_boarding_pass


def test_parse_boarding_pass_fields_from_known_lines():
    ocr_result = {
        "lines": [
            {"text": "BOARDING PASS", "score": 0.99, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "03DEC", "score": 0.99, "box": [[0, 30], [50, 30], [50, 50], [0, 50]]},
            {"text": "MU 2379", "score": 0.99, "box": [[60, 30], [130, 30], [130, 50], [60, 50]]},
            {"text": "TAIYUAN", "score": 0.99, "box": [[0, 60], [90, 60], [90, 80], [0, 80]]},
            {"text": "FUZHOU", "score": 0.99, "box": [[100, 60], [180, 60], [180, 80], [100, 80]]},
            {"text": "姓名 NAME", "score": 0.98, "box": [[0, 90], [80, 90], [80, 110], [0, 110]]},
            {"text": "ZHANGQIWEI", "score": 0.97, "box": [[90, 90], [220, 90], [220, 110], [90, 110]]},
            {"text": "ETKT 7813699238489/1", "score": 0.96, "box": [[0, 120], [220, 120], [220, 140], [0, 140]]},
            {"text": "G11", "score": 0.99, "box": [[230, 60], [260, 60], [260, 80], [230, 80]]},
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
