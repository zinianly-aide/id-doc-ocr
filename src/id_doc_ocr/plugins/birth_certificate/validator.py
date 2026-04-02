from __future__ import annotations

import re

from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


VALID_SEX = {"男", "女"}
CERT_NO_RE = re.compile(r"^[A-Z]{1,2}\d{8,10}$")
SHANGHAI_HINTS = ("上海", "浦东", "徐汇", "黄浦", "静安", "长宁", "普陀", "虹口", "杨浦", "闵行", "宝山", "嘉定", "金山", "松江", "青浦", "奉贤", "崇明")


def validate_birth_certificate(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []

    for field in ["child_name", "sex", "date_of_birth", "birth_place", "mother_name"]:
        if not fields.get(field):
            issues.append(
                ValidationIssue(
                    code=f"missing_{field}",
                    message=f"missing {field}",
                    severity="error",
                    field_name=field,
                )
            )

    sex = fields.get("sex")
    if sex and sex not in VALID_SEX:
        issues.append(
            ValidationIssue(code="invalid_sex", message="invalid sex", severity="error", field_name="sex")
        )

    gestational_weeks = fields.get("gestational_weeks")
    if gestational_weeks is not None and not (20 <= gestational_weeks <= 45):
        issues.append(
            ValidationIssue(
                code="gestational_weeks_out_of_range",
                message="gestational weeks out of range",
                severity="warning",
                field_name="gestational_weeks",
            )
        )

    birth_weight_grams = fields.get("birth_weight_grams")
    if birth_weight_grams is not None and not (500 <= birth_weight_grams <= 6500):
        issues.append(
            ValidationIssue(
                code="birth_weight_out_of_range",
                message="birth weight out of range",
                severity="warning",
                field_name="birth_weight_grams",
            )
        )

    mother_age = fields.get("mother_age")
    if mother_age is not None and not (12 <= mother_age <= 70):
        issues.append(
            ValidationIssue(
                code="mother_age_out_of_range",
                message="mother age out of range",
                severity="warning",
                field_name="mother_age",
            )
        )

    certificate_number = fields.get("certificate_number")
    if certificate_number and not CERT_NO_RE.match(str(certificate_number).strip().upper()):
        issues.append(
            ValidationIssue(
                code="certificate_number_format_suspect",
                message="certificate number format suspect",
                severity="warning",
                field_name="certificate_number",
            )
        )

    text_candidates = [fields.get("birth_place") or "", fields.get("issuing_unit") or ""]
    if any(text_candidates) and not any(hint in text for text in text_candidates for hint in SHANGHAI_HINTS):
        issues.append(
            ValidationIssue(
                code="not_shanghai_style",
                message="document lacks shanghai-style location hints",
                severity="warning",
                field_name="birth_place",
            )
        )

    accepted = not any(issue.severity == "error" for issue in issues)
    score = 1.0 if not issues else 0.85 if accepted else 0.0
    return ValidationReport(accepted=accepted, score=score, issues=issues)
