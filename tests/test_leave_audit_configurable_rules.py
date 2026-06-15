from id_doc_ocr.verification.rules import DEFAULT_RULE_CONFIGS, verify_attachment


def test_name_candidate_accepts_generic_name_field():
    analysis = {
        "classification_evidence": {"attachment_label": "MEDICAL_CERTIFICATE"},
        "extracted_fields": [{"name": "name", "value": "张三"}],
        "risk": {"score": 0},
    }
    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "expected_attachment_types": ["MEDICAL_CERTIFICATE"],
        },
    )
    applicant_rule = next(rule for rule in result["rule_results"] if rule["rule_code"] == "applicant_name_match")
    assert applicant_rule["passed"] is True


def test_marriage_config_rejects_leave_outside_registration_window():
    analysis = {
        "classification_evidence": {"attachment_label": "MARRIAGE_CERTIFICATE"},
        "extracted_fields": [
            {"name": "holder_name", "value": "张三"},
            {"name": "person_a_name", "value": "张三"},
            {"name": "person_b_name", "value": "李四"},
            {"name": "registration_date", "value": "2025-01-01"},
            {"name": "certificate_title", "value": "结婚证"},
            {"name": "registration_authority", "value": "上海市民政局"},
        ],
        "validation": {"accepted": True, "issues": []},
        "risk": {"score": 0},
    }
    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2026-01-02",
            "leave_end_date": "2026-01-03",
            "expected_attachment_types": ["MARRIAGE_CERTIFICATE"],
        },
        rule_config=DEFAULT_RULE_CONFIGS["MARRIAGE"],
    )
    assert result["verify_status"] == "REJECT"
    assert any(rule["rule_code"] == "marriage_registration_date_window" and not rule["passed"] for rule in result["rule_results"])


def test_marriage_config_allows_leave_inside_registration_window():
    analysis = {
        "classification_evidence": {"attachment_label": "MARRIAGE_CERTIFICATE"},
        "extracted_fields": [
            {"name": "holder_name", "value": "张三"},
            {"name": "person_a_name", "value": "张三"},
            {"name": "person_b_name", "value": "李四"},
            {"name": "registration_date", "value": "2026-01-01"},
            {"name": "certificate_title", "value": "结婚证"},
            {"name": "registration_authority", "value": "上海市民政局"},
        ],
        "validation": {"accepted": True, "issues": []},
        "risk": {"score": 0},
    }
    result = verify_attachment(
        analysis,
        {
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
            "expected_attachment_types": ["MARRIAGE_CERTIFICATE"],
        },
        rule_config=DEFAULT_RULE_CONFIGS["MARRIAGE"],
    )
    assert result["verify_status"] == "PASS"
    assert all(rule["passed"] for rule in result["rule_results"])
