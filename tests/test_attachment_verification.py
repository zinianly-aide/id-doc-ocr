from id_doc_ocr.verification.rules import verify_attachment


def _build_analysis(*, attachment_label: str, extracted_fields: dict, review_action: str = "accept_with_warning") -> dict:
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
            "validation_accepted": True,
        },
        "review": {"warnings": [], "evidence": {"fields": []}},
        "validation": {"accepted": True, "issues": []},
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
        extracted_fields={"holder_name": "张三", "registration_date": "2024-05-20"},
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
