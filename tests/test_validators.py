from id_doc_ocr.plugins.hukou_booklet.validator import validate_hukou_booklet
from id_doc_ocr.plugins.medical_record.validator import validate_medical_record
from id_doc_ocr.plugins.train_ticket.validator import validate_train_ticket


def test_train_ticket_missing_required_fields():
    report = validate_train_ticket({})
    assert report.accepted is False
    assert len(report.issues) >= 1


def test_medical_record_requires_patient_name():
    report = validate_medical_record({"visit_date": "2026-03-11"})
    assert report.accepted is False


def test_hukou_booklet_accepts_warning_only_result():
    report = validate_hukou_booklet(
        {
            "member_name": "李四",
            "householder_name": "张三",
            "birth_date": "2010-01-01",
        }
    )
    assert report.accepted is True
    assert {issue.code for issue in report.issues} == {"missing_household_id", "missing_id_number"}


def test_hukou_booklet_rejects_invalid_id_number():
    report = validate_hukou_booklet(
        {
            "member_name": "李四",
            "gender": "男",
            "relation_to_head": "之子",
            "id_number": "110105201001011231",
        }
    )
    assert report.accepted is False
    assert any(issue.code == "checksum_invalid" for issue in report.issues)


def test_hukou_booklet_warns_when_birth_date_mismatches_id_number():
    report = validate_hukou_booklet(
        {
            "member_name": "李四",
            "id_number": "110105201001011232",
            "birth_date": "2010-01-02",
        }
    )
    assert any(issue.code == "birth_date_mismatch" for issue in report.issues)
