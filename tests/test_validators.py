from id_doc_ocr.plugins.medical_record.validator import validate_medical_record
from id_doc_ocr.plugins.train_ticket.validator import validate_train_ticket


def test_train_ticket_missing_required_fields():
    report = validate_train_ticket({})
    assert report.accepted is False
    assert len(report.issues) >= 1


def test_medical_record_requires_patient_name():
    report = validate_medical_record({"visit_date": "2026-03-11"})
    assert report.accepted is False
