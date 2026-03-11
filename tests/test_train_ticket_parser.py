from id_doc_ocr.plugins.train_ticket.parser import parse_train_ticket_fields


def test_parse_train_ticket_fields_from_known_lines():
    ocr_result = {
        "lines": [
            {"text": "BOARDING PASS"},
            {"text": "MU 2379"},
            {"text": "03DEC"},
            {"text": "TAIYUAN"},
            {"text": "FUZHOU"},
            {"text": "ZHANGQIWEI"},
            {"text": "ETKT 7813699238489/1"},
            {"text": "G11"},
        ]
    }
    fields = parse_train_ticket_fields(ocr_result)
    assert fields["document_variant"] == "boarding_pass"
    assert fields["train_number"] == "MU2379"
    assert fields["ticket_number"] == "7813699238489/1"
    assert fields["departure_station"] == "TAIYUAN"
    assert fields["arrival_station"] == "FUZHOU"
