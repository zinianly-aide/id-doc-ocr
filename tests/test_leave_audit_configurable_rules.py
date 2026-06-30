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


def test_configured_required_field_can_reject_missing_fields():
    analysis = {
        "classification_evidence": {"attachment_label": "MEDICAL_CERTIFICATE"},
        "extracted_fields": [{"name": "patient_name", "value": "张三"}],
        "risk": {"score": 0},
    }

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "expected_attachment_types": ["MEDICAL_CERTIFICATE"],
        },
        rule_config={
            "enabled": True,
            "rules": [
                {
                    "type": "required_field",
                    "rule_code": "sick_required_dates",
                    "fields": ["rest_start_date", "rest_end_date"],
                    "on_fail": "REJECT",
                }
            ],
        },
    )

    assert result["verify_status"] == "REJECT"
    rule = next(rule for rule in result["rule_results"] if rule["rule_code"] == "sick_required_dates")
    assert rule["passed"] is False
    assert rule["evidence"]["present"] == {"rest_start_date": False, "rest_end_date": False}


def test_configured_date_coverage_allows_document_period_covering_leave():
    analysis = {
        "classification_evidence": {"attachment_label": "MEDICAL_CERTIFICATE"},
        "extracted_fields": [
            {"name": "patient_name", "value": "张三"},
            {"name": "rest_start_date", "value": "2026-04-01"},
            {"name": "rest_end_date", "value": "2026-04-05"},
        ],
        "risk": {"score": 0},
    }

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-02",
            "leave_end_date": "2026-04-04",
            "expected_attachment_types": ["MEDICAL_CERTIFICATE"],
        },
        rule_config={
            "enabled": True,
            "rules": [
                {
                    "type": "date_coverage",
                    "rule_code": "sick_rest_period_covers_leave",
                    "on_fail": "REVIEW",
                }
            ],
        },
    )

    assert result["verify_status"] == "PASS"
    assert any(rule["rule_code"] == "sick_rest_period_covers_leave" and rule["passed"] for rule in result["rule_results"])


def test_configured_field_equals_can_compare_against_request_field():
    analysis = {
        "classification_evidence": {"attachment_label": "MEDICAL_CERTIFICATE"},
        "extracted_fields": [
            {"name": "patient_name", "value": "张三"},
            {"name": "rest_start_date", "value": "2026-04-01"},
            {"name": "rest_end_date", "value": "2026-04-03"},
        ],
        "risk": {"score": 0},
    }

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
            "expected_attachment_types": ["MEDICAL_CERTIFICATE"],
        },
        rule_config={
            "enabled": True,
            "rules": [
                {
                    "type": "field_equals",
                    "rule_code": "patient_name_equals_applicant",
                    "field": "patient_name",
                    "request_field": "applicant_name",
                    "on_fail": "REJECT",
                }
            ],
        },
    )

    assert result["verify_status"] == "PASS"
    assert any(rule["rule_code"] == "patient_name_equals_applicant" and rule["passed"] for rule in result["rule_results"])


def test_configured_field_contains_can_match_any_expected_keyword():
    analysis = {
        "classification_evidence": {"attachment_label": "MEDICAL_CERTIFICATE"},
        "extracted_fields": [
            {"name": "patient_name", "value": "张三"},
            {"name": "diagnosis", "value": ["急性上呼吸道感染"]},
            {"name": "rest_start_date", "value": "2026-04-01"},
            {"name": "rest_end_date", "value": "2026-04-03"},
        ],
        "risk": {"score": 0},
    }

    result = verify_attachment(
        analysis,
        {
            "leave_type": "SICK",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
            "expected_attachment_types": ["MEDICAL_CERTIFICATE"],
        },
        rule_config={
            "enabled": True,
            "rules": [
                {
                    "type": "field_contains",
                    "rule_code": "diagnosis_has_illness_signal",
                    "field": "diagnosis",
                    "any_of": ["感染", "发热"],
                    "on_fail": "REVIEW",
                }
            ],
        },
    )

    assert result["verify_status"] == "PASS"
    assert any(rule["rule_code"] == "diagnosis_has_illness_signal" and rule["passed"] for rule in result["rule_results"])
