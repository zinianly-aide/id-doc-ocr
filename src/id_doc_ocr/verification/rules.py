from __future__ import annotations

from datetime import date
from typing import Any


NAME_FIELD_CANDIDATES = (
    "name",
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
    "PATERNITY": ["BIRTH_CERTIFICATE"],
    "PARENTAL": ["BIRTH_CERTIFICATE"],
    "BEREAVEMENT": ["CUSTODY_RELATIONSHIP_CERTIFICATE", "HUKOU_BOOKLET"],
}

RULE_CODE_ZH_MESSAGES = {
    "attachment_type_match": {
        True: "材料类型符合该假别要求",
        False: "材料类型与该假别要求不一致",
    },
    "applicant_name_match": {
        True: "申请人与材料中的人员信息一致",
        False: "申请人与材料中的人员信息不一致",
    },
    "leave_date_match": {
        True: "请假日期与材料日期信息一致",
        False: "请假日期与材料日期信息不一致",
    },
    "related_person_match": {
        True: "关联人员信息与材料信息一致",
        False: "关联人员信息与材料信息不一致",
    },
}


DEFAULT_FIELD_MAPPING_CONFIG: dict[str, list[str]] = {
    "applicant_name": list(NAME_FIELD_CANDIDATES),
    "related_person_name": list(RELATED_PERSON_FIELD_CANDIDATES),
    "leave_start_date": list(START_DATE_FIELD_CANDIDATES),
    "leave_end_date": list(END_DATE_FIELD_CANDIDATES),
}

DEFAULT_RULE_CONFIGS: dict[str, dict[str, Any]] = {
    "MARRIAGE": {
        "leave_type": "MARRIAGE",
        "prompt_text": "核验婚假材料时，优先确认结婚登记日期、请假起止日期和请假人姓名是否满足公司婚假规则。",
        "enabled": True,
        "rules": [
            {
                "type": "date_window",
                "rule_code": "marriage_registration_date_window",
                "date_field": "registration_date",
                "max_years": 1,
                "on_fail": "REJECT",
                "message": "marriage leave dates must be within one year after registration date",
                "message_zh": "婚假日期必须在结婚登记日期起一年内",
            },
            {
                "type": "required_name",
                "rule_code": "marriage_applicant_name_present",
                "on_fail": "REJECT",
                "message": "marriage certificate must contain applicant name",
                "message_zh": "婚假附件必须出现请假人姓名",
            },
        ],
    }
}


def _field_map(analysis: dict[str, Any]) -> dict[str, Any]:
    return {field.get("name"): field.get("value") for field in analysis.get("extracted_fields", []) if isinstance(field, dict)}



def _pick_first(fields: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        value = fields.get(name)
        if value not in (None, "", []):
            return value
    return None


def _candidates(config: dict[str, list[str]] | None, key: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
    configured = (config or {}).get(key)
    if configured:
        return tuple(str(item) for item in configured if str(item).strip())
    return fallback


def _parse_date(value: Any) -> date | None:
    if value in (None, "", []):
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _field_names(rule: dict[str, Any], *keys: str, default: str | None = None) -> list[str]:
    for key in keys:
        value = rule.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [item.strip() for item in value.split(",") if item.strip()]
    return [default] if default else []


def _rule_expected_value(rule: dict[str, Any], request: dict[str, Any]) -> Any:
    if "expected" in rule:
        return rule.get("expected")
    if "expected_value" in rule:
        return rule.get("expected_value")
    request_field = rule.get("request_field")
    if request_field:
        return request.get(str(request_field))
    return None


def _contains_text(value: Any, expected: Any) -> bool:
    if expected in (None, "", []):
        return False
    if isinstance(expected, list):
        return any(_contains_text(value, item) for item in expected)
    if isinstance(value, list):
        return any(_contains_text(item, expected) for item in value)
    return str(expected) in str(value or "")


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + years)



def _build_rule(rule_code: str, passed: bool, severity: str, score_delta: int, message: str, evidence: dict[str, Any]) -> dict[str, Any]:
    message_zh = RULE_CODE_ZH_MESSAGES.get(rule_code, {}).get(bool(passed), message)
    return {
        "rule_code": rule_code,
        "passed": passed,
        "severity": severity,
        "score_delta": score_delta,
        "message": message,
        "message_zh": message_zh,
        "display_message": message_zh,
        "evidence": evidence,
    }


def _build_config_rule(rule: dict[str, Any], passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    rule_code = str(rule.get("rule_code") or rule.get("type") or "configured_rule")
    on_fail = str(rule.get("on_fail") or "REVIEW").upper()
    severity = "error" if on_fail == "REJECT" else "warning"
    message = str(rule.get("message") or rule_code)
    result = _build_rule(rule_code, passed, severity if not passed else "info", int(rule.get("score_delta") or (80 if severity == "error" else 35)), message, evidence)
    if rule.get("message_zh"):
        result["message_zh"] = str(rule["message_zh"])
        result["display_message"] = str(rule["message_zh"])
    return result


def _apply_configured_rules(
    request: dict[str, Any],
    fields: dict[str, Any],
    extracted_name: Any,
    rule_config: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], str | None]:
    if not rule_config or not rule_config.get("enabled", True):
        return [], None
    configured_results: list[dict[str, Any]] = []
    forced_status: str | None = None
    for rule in rule_config.get("rules") or []:
        if not isinstance(rule, dict):
            continue
        rule_type = str(rule.get("type") or "")
        passed = True
        evidence: dict[str, Any] = {}
        if rule_type == "date_window":
            date_field = str(rule.get("date_field") or "registration_date")
            registration_date = _parse_date(fields.get(date_field))
            leave_start_date = _parse_date(request.get("leave_start_date"))
            leave_end_date = _parse_date(request.get("leave_end_date"))
            max_years = int(rule.get("max_years") or 1)
            window_end = _add_years(registration_date, max_years) if registration_date else None
            passed = bool(registration_date and leave_start_date and leave_end_date and leave_start_date >= registration_date and window_end and leave_end_date <= window_end)
            evidence = {
                "date_field": date_field,
                "registration_date": fields.get(date_field),
                "leave_start_date": request.get("leave_start_date"),
                "leave_end_date": request.get("leave_end_date"),
                "window_end_date": window_end.isoformat() if window_end else None,
            }
        elif rule_type == "required_name":
            applicant_name = request.get("applicant_name")
            configured_candidates = tuple(str(item) for item in rule.get("candidates", []) if str(item).strip())
            candidate_value = _pick_first(fields, configured_candidates) if configured_candidates else extracted_name
            values = [str(value) for value in fields.values() if value not in (None, "", [])]
            passed = bool(applicant_name and (candidate_value == applicant_name or str(applicant_name) in values))
            evidence = {
                "applicant_name": applicant_name,
                "extracted_name": candidate_value,
                "configured_candidates": list(configured_candidates),
            }
        elif rule_type == "required_field":
            required_fields = _field_names(rule, "fields", "field")
            mode = str(rule.get("mode") or "all").lower()
            present = {field_name: fields.get(field_name) not in (None, "", []) for field_name in required_fields}
            passed = any(present.values()) if mode == "any" else all(present.values())
            evidence = {
                "required_fields": required_fields,
                "mode": mode,
                "present": present,
            }
        elif rule_type == "date_coverage":
            document_start_field = str(rule.get("document_start_field") or rule.get("start_field") or "rest_start_date")
            document_end_field = str(rule.get("document_end_field") or rule.get("end_field") or "rest_end_date")
            request_start_field = str(rule.get("request_start_field") or "leave_start_date")
            request_end_field = str(rule.get("request_end_field") or "leave_end_date")
            document_start_date = _parse_date(fields.get(document_start_field))
            document_end_date = _parse_date(fields.get(document_end_field))
            request_start_date = _parse_date(request.get(request_start_field))
            request_end_date = _parse_date(request.get(request_end_field))
            passed = bool(
                document_start_date
                and document_end_date
                and request_start_date
                and request_end_date
                and document_start_date <= request_start_date
                and document_end_date >= request_end_date
            )
            evidence = {
                "document_start_field": document_start_field,
                "document_end_field": document_end_field,
                "request_start_field": request_start_field,
                "request_end_field": request_end_field,
                "document_start_date": fields.get(document_start_field),
                "document_end_date": fields.get(document_end_field),
                "request_start_date": request.get(request_start_field),
                "request_end_date": request.get(request_end_field),
            }
        elif rule_type == "field_equals":
            field_name = str(rule.get("field") or "")
            expected = _rule_expected_value(rule, request)
            actual = fields.get(field_name)
            passed = bool(field_name and actual == expected)
            evidence = {
                "field": field_name,
                "actual": actual,
                "expected": expected,
                "request_field": rule.get("request_field"),
            }
        elif rule_type == "field_contains":
            field_name = str(rule.get("field") or "")
            expected = rule.get("contains")
            if expected is None:
                expected = rule.get("any_of")
            if expected is None:
                expected = _rule_expected_value(rule, request)
            actual = fields.get(field_name)
            passed = bool(field_name and _contains_text(actual, expected))
            evidence = {
                "field": field_name,
                "actual": actual,
                "expected": expected,
                "request_field": rule.get("request_field"),
            }
        else:
            continue
        result = _build_config_rule(rule, passed, evidence)
        configured_results.append(result)
        if not passed and str(rule.get("on_fail") or "REVIEW").upper() == "REJECT":
            forced_status = "REJECT"
    return configured_results, forced_status


def _build_auto_pass_readiness(verify_status: str, rule_results: list[dict[str, Any]]) -> dict[str, Any]:
    failed_rules = [rule for rule in rule_results if not rule.get("passed")]
    blockers = [rule.get("display_message") or rule.get("message") for rule in failed_rules if rule.get("severity") == "error"]
    reasons = [rule.get("display_message") or rule.get("message") for rule in failed_rules if rule.get("severity") != "error"]
    if verify_status == "PASS" and not failed_rules:
        return {"status": "ready", "label": "可自动通过", "reasons": [], "blockers": []}
    if blockers or verify_status in {"REJECT", "ERROR"}:
        return {"status": "blocked", "label": "禁止自动通过", "reasons": reasons, "blockers": blockers}
    return {"status": "unknown", "label": "需要人工确认", "reasons": reasons, "blockers": []}



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



def verify_attachment(
    analysis: dict[str, Any],
    request: dict[str, Any],
    field_mapping_config: dict[str, list[str]] | None = None,
    rule_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields = _field_map(analysis)
    classification = analysis.get("classification_evidence") or {}
    predicted_type = classification.get("attachment_label") or "UNKNOWN"
    expected_types = _resolve_expected_attachment_types(request)
    applicant_name = request.get("applicant_name")
    related_person_name = request.get("related_person_name")
    related_person_relation = request.get("related_person_relation")
    extracted_name = _pick_first(fields, _candidates(field_mapping_config, "applicant_name", NAME_FIELD_CANDIDATES))
    extracted_related_person_name = _pick_first(fields, _candidates(field_mapping_config, "related_person_name", RELATED_PERSON_FIELD_CANDIDATES))
    leave_start_date = request.get("leave_start_date")
    leave_end_date = request.get("leave_end_date")
    extracted_start_date = _pick_first(fields, _candidates(field_mapping_config, "leave_start_date", START_DATE_FIELD_CANDIDATES))
    extracted_end_date = _pick_first(fields, _candidates(field_mapping_config, "leave_end_date", END_DATE_FIELD_CANDIDATES))

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

    configured_rules = (rule_config or {}).get("rules") or []
    has_configured_date_window = any(isinstance(rule, dict) and rule.get("type") == "date_window" for rule in configured_rules)
    has_configured_date_coverage = any(isinstance(rule, dict) and rule.get("type") == "date_coverage" for rule in configured_rules)
    date_match = True
    if not has_configured_date_window and not has_configured_date_coverage:
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

    configured_rule_results, forced_status = _apply_configured_rules(request, fields, extracted_name, rule_config)
    rule_results.extend(configured_rule_results)

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
    if forced_status:
        verify_status = forced_status

    warnings = [rule["display_message"] for rule in rule_results if not rule["passed"]]
    request_evidence = dict(request)
    request_evidence["resolved_expected_attachment_types"] = expected_types
    auto_pass_readiness = _build_auto_pass_readiness(verify_status, rule_results)
    return {
        "verify_status": verify_status,
        "risk_score": total_risk,
        "risk_level": _risk_level(total_risk),
        "autoPassReadiness": auto_pass_readiness,
        "matched_attachment_type": predicted_type,
        "extracted_fields": fields,
        "rule_results": rule_results,
        "warnings": warnings,
        "evidence": {
            "classification": classification,
            "request": request_evidence,
            "fields": fields,
            "field_mapping_config": field_mapping_config or DEFAULT_FIELD_MAPPING_CONFIG,
            "rule_config": rule_config,
        },
        "needs_manual_review": verify_status != "PASS",
        "summary_message": f"{verify_status}: {predicted_type} vs expected {expected_types or ['UNSPECIFIED']}",
    }
