from __future__ import annotations

from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport
from id_doc_ocr.validator.passport_mrz import build_passport_mrz_report


_COMPARABLE_FIELDS = [
    "passport_number",
    "issuing_country",
    "nationality",
    "surname",
    "given_names",
    "birth_date",
    "expiry_date",
    "sex",
]


def _normalize(value: str | None) -> str:
    return (value or "").replace(" ", "").upper()


def validate_passport(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    mrz_lines = fields.get("mrz_lines") or []
    mrz_report = None

    if len(mrz_lines) == 2:
        mrz_report = build_passport_mrz_report(mrz_lines)
        issues.extend(mrz_report.issues)
    else:
        issues.append(
            ValidationIssue(
                code="missing_mrz_lines",
                message="missing passport mrz lines",
                severity="error",
                field_name="mrz_lines",
            )
        )

    mrz_fields = fields.get("mrz_fields") or {}
    if isinstance(mrz_fields, dict):
        for field_name in _COMPARABLE_FIELDS:
            expected = mrz_fields.get(field_name)
            actual = fields.get(field_name)
            if expected is None or actual is None:
                continue
            if _normalize(expected) != _normalize(actual):
                issues.append(
                    ValidationIssue(
                        code=f"{field_name}_mismatch",
                        message=f"{field_name} does not match mrz",
                        severity="error",
                        field_name=field_name,
                    )
                )

    accepted = not any(issue.severity == "error" for issue in issues)
    score = 1.0 if accepted else 0.0
    if mrz_report and mrz_report.accepted is False and not issues:
        score = mrz_report.score
    return ValidationReport(accepted=accepted, score=score, issues=issues)
