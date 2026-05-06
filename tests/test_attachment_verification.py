from id_doc_ocr.verification.rules import verify_attachment


def _build_analysis(
    *,
    attachment_label: str,
    extracted_fields: dict,
    review_action: str = "accept_with_warning",
    validation_accepted: bool = True,
    validation_issues: list[dict] | None = None,
) -> dict:
    return {
        "doc_type": extracted_fields.get("doc_type", "diagnosis_proof"),
        "classification_evidence": {
            "attachment_label": attachment_label,
            "attachment_confidence": 0.9,
            "matched_keywords": [attachment_label],
        },
        "extracted_fields": [
            {"name": key, "value": value, "confidence": 0.95, "source": "parsed_field", "bbox": None, "evidence_text": None, "matched": False}
            for key, value in extracted_fields.items()
        ],
        "risk": {
            "score": 0.0,
            "review_action": review_action,
            "review_recommended": review_action in {"review", "reject"},
            "quality_passed": True,
            "validation_accepted": validation_accepted,
        },
        "review": {"warnings": [], "evidence": {"fields": []}},
        "validation": {"accepted": validation_accepted, "issues": validation_issues or []},
        "raw_artifacts": {},
    }



def test_verify_attachment_returns_pass_for_matching_medical_leave_request():
    analysis = _build_analysis(
        attachment_label="MEDICAL_CERTIFICATE",
        extracted_fields={
            "patient_name": "张三",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
            "issue_date": "2026-04-01",
        },
    )

    result = verify_attachment(
        analysis,
        {
            "expected_attachment_type": "MEDICAL_CERTIFICATE",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
        },
    )

    assert result["verify_status"] == "PASS"
    assert result["risk_level"] == "LOW"
    assert result["needs_manual_review"] is False
    assert all(rule["passed"] for rule in result["rule_results"])



def test_verify_attachment_returns_review_for_name_mismatch():
    analysis = _build_analysis(
        attachment_label="MEDICAL_CERTIFICATE",
        extracted_fields={
            "patient_name": "李四",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
        },
    )

    result = verify_attachment(
        analysis,
        {
            "expected_attachment_type": "MEDICAL_CERTIFICATE",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True
    assert any(rule["rule_code"] == "applicant_name_match" and rule["passed"] is False for rule in result["rule_results"])



def test_verify_attachment_returns_reject_for_attachment_type_mismatch():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={"holder_name": "张三", "registration_date": "2026-04-01"},
    )

    result = verify_attachment(
        analysis,
        {
            "expected_attachment_type": "MEDICAL_CERTIFICATE",
            "applicant_name": "张三",
        },
    )

    assert result["verify_status"] == "REJECT"
    assert result["risk_level"] == "HIGH"
    assert any(rule["rule_code"] == "attachment_type_match" and rule["severity"] == "error" for rule in result["rule_results"])



def test_verify_attachment_accepts_multiple_expected_attachment_types():
    analysis = _build_analysis(
        attachment_label="BIRTH_CERTIFICATE",
        extracted_fields={"child_name": "小宝", "date_of_birth": "2024-03-16"},
    )

    result = verify_attachment(
        analysis,
        {
            "expected_attachment_types": ["MEDICAL_CERTIFICATE", "BIRTH_CERTIFICATE"],
            "applicant_name": "张三",
        },
    )

    assert result["verify_status"] != "REJECT"
    assert any(rule["rule_code"] == "attachment_type_match" and rule["passed"] is True for rule in result["rule_results"])
    assert result["evidence"]["request"]["resolved_expected_attachment_types"] == ["MEDICAL_CERTIFICATE", "BIRTH_CERTIFICATE"]



def test_verify_attachment_uses_leave_type_default_attachment_matrix():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        },
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
        },
    )

    assert result["verify_status"] == "PASS"
    assert result["evidence"]["request"]["resolved_expected_attachment_types"] == ["MARRIAGE_CERTIFICATE"]



def test_verify_attachment_downgrades_sick_pass_to_review_when_analysis_rejects():
    analysis = _build_analysis(
        attachment_label="MEDICAL_CERTIFICATE",
        extracted_fields={
            "patient_name": "张三",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
            "issue_date": "2026-04-01",
        },
        review_action="reject",
        validation_accepted=False,
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_sick_pass_to_review_for_weak_medical_record_signal():
    analysis = _build_analysis(
        attachment_label="MEDICAL_CERTIFICATE",
        extracted_fields={
            "doc_type": "medical_record",
            "patient_name": "张三",
            "issue_date": "2026-04-01",
        },
        review_action="review",
        validation_accepted=False,
        validation_issues=[
            {"code": "not_sick_note_like"},
            {"code": "weak_sick_note_signal"},
        ],
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_sick_pass_to_review_when_minimum_fields_missing():
    analysis = _build_analysis(
        attachment_label="MEDICAL_CERTIFICATE",
        extracted_fields={
            "patient_name": None,
            "issue_date": None,
            "rest_start_date": None,
            "rest_end_date": None,
            "rest_days": None,
        },
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_when_analysis_rejects():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        },
        review_action="reject",
        validation_accepted=False,
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
            "related_person_name": "李四",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_when_minimum_fields_missing():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": None,
            "holder_name": "张三",
            "registration_date": None,
            "person_a_name": "张三",
            "person_b_name": None,
            "registration_authority": None,
        },
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_for_holder_not_in_couple_warning():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "王五",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        },
        validation_accepted=True,
        validation_issues=[{"code": "holder_name_not_in_couple"}],
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "王五",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_for_suspect_authority_warning():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "某某办公室",
        },
        validation_accepted=True,
        validation_issues=[{"code": "registration_authority_suspect"}],
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_for_suspect_title_warning():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "证明材料",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        },
        validation_accepted=True,
        validation_issues=[{"code": "certificate_title_suspect"}],
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_when_analysis_reviewed():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        },
        review_action="review",
        validation_accepted=True,
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_downgrades_marriage_pass_to_review_when_validation_not_accepted():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "中华人民共和国结婚证",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "杭州市西湖区民政局婚姻登记处",
        },
        validation_accepted=False,
    )

    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
        },
    )

    assert result["verify_status"] == "REVIEW"
    assert result["needs_manual_review"] is True



def test_verify_attachment_marriage_gating_does_not_apply_to_non_marriage_leave_type():
    analysis = _build_analysis(
        attachment_label="MARRIAGE_CERTIFICATE",
        extracted_fields={
            "certificate_title": "证明材料",
            "holder_name": "王五",
            "registration_date": "2024-05-20",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_authority": "某某办公室",
        },
        validation_accepted=True,
        validation_issues=[
            {"code": "certificate_title_suspect"},
            {"code": "holder_name_not_in_couple"},
            {"code": "registration_authority_suspect"},
        ],
    )

    result = verify_attachment(
        analysis,
        {
            "expected_attachment_type": "MARRIAGE_CERTIFICATE",
            "applicant_name": "王五",
        },
    )

    assert result["verify_status"] == "PASS"
    assert result["needs_manual_review"] is False
