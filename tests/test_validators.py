from id_doc_ocr.plugins.birth_certificate.validator import validate_birth_certificate
from id_doc_ocr.plugins.hukou_booklet.validator import validate_hukou_booklet
from id_doc_ocr.plugins.medical_record.validator import validate_medical_record
from id_doc_ocr.plugins.only_child_certificate.validator import validate_only_child_certificate
from id_doc_ocr.plugins.train_ticket.validator import validate_train_ticket


def test_train_ticket_missing_required_fields():
    report = validate_train_ticket({})
    assert report.accepted is False
    assert len(report.issues) >= 1


def test_medical_record_requires_patient_name():
    report = validate_medical_record({"visit_date": "2026-03-11"})
    assert report.accepted is False


def test_medical_record_warns_when_not_sick_note_like():
    report = validate_medical_record(
        {
            "patient_name": "张三",
            "visit_date": "2026-03-11",
            "sick_note_check": {"is_sick_note_like": False, "score": 0.25},
        }
    )
    assert report.accepted is True
    assert {issue.code for issue in report.issues} >= {"not_sick_note_like", "weak_sick_note_signal"}
    assert report.score == 0.625


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


def test_birth_certificate_requires_core_fields():
    report = validate_birth_certificate({"sex": "男"})
    assert report.accepted is False
    assert {issue.code for issue in report.issues} >= {
        "missing_child_name",
        "missing_date_of_birth",
        "missing_birth_place",
        "missing_mother_name",
    }


def test_birth_certificate_warns_when_not_shanghai_style():
    report = validate_birth_certificate(
        {
            "child_name": "Baby A",
            "sex": "女",
            "date_of_birth": "2024-03-16",
            "birth_place": "杭州市妇产科医院",
            "mother_name": "王芳",
            "certificate_number": "T310123456",
        }
    )
    assert report.accepted is True
    assert any(issue.code == "not_shanghai_style" for issue in report.issues)


def test_only_child_certificate_requires_core_fields():
    report = validate_only_child_certificate({"child_gender": "男"})
    assert report.accepted is False
    assert {issue.code for issue in report.issues} >= {
        "missing_child_name",
        "missing_child_birth_date",
        "missing_father_name",
        "missing_mother_name",
    }


def test_only_child_certificate_warns_when_not_east_china_style():
    report = validate_only_child_certificate(
        {
            "certificate_title": "独生子女父母光荣证",
            "child_name": "安小宁",
            "child_gender": "女",
            "child_birth_date": "2020-06-18",
            "father_name": "李强",
            "mother_name": "张敏",
            "issuing_authority": "成都市某街道办事处",
        }
    )
    assert report.accepted is True
    assert any(issue.code == "not_east_china_style" for issue in report.issues)
