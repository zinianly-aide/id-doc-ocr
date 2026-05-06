from __future__ import annotations

from typing import Any


NAME_FIELD_CANDIDATES = (
    "patient_name",
    "holder_name",
    "person_a_name",
    "person_b_name",
    "child_name",
)
RELATED_PERSON_FIELD_CANDIDATES = (
    "person_b_name",
    "father_name",
    "mother_name",
)
START_DATE_FIELD_CANDIDATES = ("rest_start_date", "registration_date", "issue_date", "date_of_birth")
END_DATE_FIELD_CANDIDATES = ("rest_end_date", "registration_date", "issue_date", "date_of_birth")
LEAVE_TYPE_ATTACHMENT_MATRIX = {
    "SICK": ["MEDICAL_CERTIFICATE"],
    "MARRIAGE": ["MARRIAGE_CERTIFICATE"],
    "MATERNITY": ["BIRTH_CERTIFICATE", "MEDICAL_CERTIFICATE"],
}



def _field_map(analysis: dict[str, Any]) -> dict[str, Any]:
    return {field.get("name"): field.get("value") for field in analysis.get("extracted_fields", []) if isinstance(field, dict)}



def _pick_first(fields: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        value = fields.get(name)
        if value not in (None, "", []):
            return value
    return None



def _build_rule(rule_code: str, passed: bool, severity: str, score_delta: int, message: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_code": rule_code,
        "passed": passed,
        "severity": severity,
        "score_delta": score_delta,
        "message": message,
        "evidence": evidence,
    }



def _resolve_expected_attachment_types(request: dict[str, Any]) -> list[str]:
    if isinstance(request.get("expected_attachment_types"), list):
        return [str(item) for item in request["expected_attachment_types"] if item]
    if isinstance(request.get("expected_attachment_types"), str) and request.get("expected_attachment_types").strip():
        return [item.strip() for item in request["expected_attachment_types"].split(",") if item.strip()]
    if request.get("expected_attachment_type"):
        return [str(request["expected_attachment_type"])]
    leave_type = str(request.get("leave_type") or "").upper()
    return LEAVE_TYPE_ATTACHMENT_MATRIX.get(leave_type, [])



def _risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"



def _issue_codes(analysis: dict[str, Any]) -> set[str]:
    validation = analysis.get("validation") or {}
    issues = validation.get("issues") or []
    codes: set[str] = set()
    for issue in issues:
        if isinstance(issue, dict) and issue.get("code"):
            codes.add(str(issue["code"]))
    return codes



def _apply_sick_pass_gating(analysis: dict[str, Any], request: dict[str, Any], fields: dict[str, Any], verify_status: str) -> str:
    if str(request.get("leave_type") or "").upper() != "SICK":
        return verify_status
    if verify_status != "PASS":
        return verify_status

    review_action = str((analysis.get("risk") or {}).get("review_action") or "")
    if review_action == "reject":
        return "REVIEW"

    if analysis.get("doc_type") == "medical_record":
        issue_codes = _issue_codes(analysis)
        if "not_sick_note_like" in issue_codes or "weak_sick_note_signal" in issue_codes:
            return "REVIEW"

    patient_name = fields.get("patient_name")
    has_leave_evidence = any(
        fields.get(field_name) not in (None, "", [])
        for field_name in ("rest_start_date", "rest_end_date", "rest_days", "issue_date")
    )
    if not patient_name or not has_leave_evidence:
        return "REVIEW"

    return verify_status



def _apply_marriage_pass_gating(analysis: dict[str, Any], request: dict[str, Any], fields: dict[str, Any], verify_status: str) -> str:
    if str(request.get("leave_type") or "").upper() != "MARRIAGE":
        return verify_status
    if verify_status != "PASS":
        return verify_status

    review_action = str((analysis.get("risk") or {}).get("review_action") or "")
    if review_action in {"review", "reject"}:
        return "REVIEW"

    validation = analysis.get("validation") or {}
    if not bool(validation.get("accepted", True)):
        return "REVIEW"

    minimum_required_fields = (
        "certificate_title",
        "holder_name",
        "registration_date",
        "person_a_name",
        "person_b_name",
        "registration_authority",
    )
    if any(fields.get(field_name) in (None, "", []) for field_name in minimum_required_fields):
        return "REVIEW"

    issue_codes = _issue_codes(analysis)
    review_blocking_issue_codes = {
        "holder_name_not_in_couple",
        "registration_authority_suspect",
        "certificate_title_suspect",
    }
    if issue_codes & review_blocking_issue_codes:
        return "REVIEW"

    return verify_status



def verify_attachment(analysis: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    fields = _field_map(analysis)
    classification = analysis.get("classification_evidence") or {}
    predicted_type = classification.get("attachment_label") or "UNKNOWN"
    expected_types = _resolve_expected_attachment_types(request)
    applicant_name = request.get("applicant_name")
    related_person_name = request.get("related_person_name")
    related_person_relation = request.get("related_person_relation")
    extracted_name = _pick_first(fields, NAME_FIELD_CANDIDATES)
    extracted_related_person_name = _pick_first(fields, RELATED_PERSON_FIELD_CANDIDATES)
    leave_start_date = request.get("leave_start_date")
    leave_end_date = request.get("leave_end_date")
    extracted_start_date = _pick_first(fields, START_DATE_FIELD_CANDIDATES)
    extracted_end_date = _pick_first(fields, END_DATE_FIELD_CANDIDATES)

    rule_results: list[dict[str, Any]] = []

    type_match = (not expected_types) or predicted_type in expected_types
    rule_results.append(
        _build_rule(
            "attachment_type_match",
            type_match,
            "error" if not type_match else "info",
            80 if not type_match else 0,
            "attachment type matches expected leave attachment" if type_match else "attachment type does not match expected leave attachment",
            {"expected_attachment_types": expected_types, "predicted_attachment_type": predicted_type},
        )
    )

    name_match = (not applicant_name) or (extracted_name == applicant_name)
    rule_results.append(
        _build_rule(
            "applicant_name_match",
            name_match,
            "warning" if not name_match else "info",
            35 if not name_match else 0,
            "applicant name matches extracted document identity" if name_match else "applicant name does not match extracted document identity",
            {"applicant_name": applicant_name, "extracted_name": extracted_name},
        )
    )

    date_match = True
    if leave_start_date and extracted_start_date and leave_start_date != extracted_start_date:
        date_match = False
    if leave_end_date and extracted_end_date and leave_end_date != extracted_end_date:
        date_match = False
    rule_results.append(
        _build_rule(
            "leave_date_match",
            date_match,
            "warning" if not date_match else "info",
            25 if not date_match else 0,
            "leave dates align with extracted document dates" if date_match else "leave dates do not align with extracted document dates",
            {
                "leave_start_date": leave_start_date,
                "leave_end_date": leave_end_date,
                "extracted_start_date": extracted_start_date,
                "extracted_end_date": extracted_end_date,
            },
        )
    )

    related_person_match = (not related_person_name) or (extracted_related_person_name == related_person_name)
    rule_results.append(
        _build_rule(
            "related_person_match",
            related_person_match,
            "warning" if not related_person_match else "info",
            30 if not related_person_match else 0,
            "related person matches extracted document relationship party" if related_person_match else "related person does not match extracted document relationship party",
            {
                "related_person_name": related_person_name,
                "related_person_relation": related_person_relation,
                "extracted_related_person_name": extracted_related_person_name,
            },
        )
    )

    base_risk = int(round(float((analysis.get("risk") or {}).get("score") or 0)))
    total_risk = min(100, base_risk + sum(rule["score_delta"] for rule in rule_results if not rule["passed"]))
    has_error = any((not rule["passed"]) and rule["severity"] == "error" for rule in rule_results)
    has_warning = any((not rule["passed"]) and rule["severity"] == "warning" for rule in rule_results)

    if has_error:
        verify_status = "REJECT"
    elif has_warning:
        verify_status = "REVIEW"
    else:
        verify_status = "PASS"

    verify_status = _apply_sick_pass_gating(analysis, request, fields, verify_status)
    verify_status = _apply_marriage_pass_gating(analysis, request, fields, verify_status)

    warnings = [rule["message"] for rule in rule_results if not rule["passed"]]
    request_evidence = dict(request)
    request_evidence["resolved_expected_attachment_types"] = expected_types
    return {
        "verify_status": verify_status,
        "risk_score": total_risk,
        "risk_level": _risk_level(total_risk),
        "matched_attachment_type": predicted_type,
        "extracted_fields": fields,
        "rule_results": rule_results,
        "warnings": warnings,
        "evidence": {
            "classification": classification,
            "request": request_evidence,
            "fields": fields,
        },
        "needs_manual_review": verify_status != "PASS",
        "summary_message": f"{verify_status}: {predicted_type} vs expected {expected_types or ['UNSPECIFIED']}",
    }
