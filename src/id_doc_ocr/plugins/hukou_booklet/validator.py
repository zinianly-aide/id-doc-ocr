from __future__ import annotations

from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport
from id_doc_ocr.validator.china_id import validate_china_id_number


RELATION_TOKENS = {
    "户主",
    "之妻",
    "之夫",
    "之子",
    "之女",
    "子",
    "女",
    "孙子",
    "孙女",
    "父亲",
    "母亲",
    "配偶",
    "非亲属",
}
GENDER_TOKENS = {"男", "女"}


def _birth_from_id(id_number: str | None) -> str | None:
    if not id_number or len(id_number) != 18 or not id_number[:17].isdigit():
        return None
    return f"{id_number[6:10]}-{id_number[10:12]}-{id_number[12:14]}"


def validate_hukou_booklet(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []

    if not fields.get("member_name") and not fields.get("householder_name"):
        issues.append(
            ValidationIssue(
                code="missing_member_name",
                message="missing member name",
                severity="error",
                field_name="member_name",
            )
        )

    if not fields.get("household_id"):
        issues.append(
            ValidationIssue(
                code="missing_household_id",
                message="missing household id",
                severity="warning",
                field_name="household_id",
            )
        )

    gender = fields.get("gender")
    if gender and gender not in GENDER_TOKENS:
        issues.append(
            ValidationIssue(
                code="invalid_gender",
                message="invalid gender",
                severity="warning",
                field_name="gender",
            )
        )

    relation = fields.get("relation_to_head")
    if relation and not any(token in relation for token in RELATION_TOKENS):
        issues.append(
            ValidationIssue(
                code="invalid_relation_to_head",
                message="invalid relation to head",
                severity="warning",
                field_name="relation_to_head",
            )
        )

    id_number = fields.get("id_number")
    if id_number:
        for code in validate_china_id_number(id_number):
            issues.append(
                ValidationIssue(
                    code=code,
                    message=code.replace("_", " "),
                    severity="error",
                    field_name="id_number",
                )
            )
        birth_date = fields.get("birth_date")
        expected_birth_date = _birth_from_id(id_number)
        if birth_date and expected_birth_date and birth_date != expected_birth_date:
            issues.append(
                ValidationIssue(
                    code="birth_date_mismatch",
                    message="birth date does not match id number",
                    severity="warning",
                    field_name="birth_date",
                )
            )
    elif fields.get("birth_date"):
        issues.append(
            ValidationIssue(
                code="missing_id_number",
                message="missing id number",
                severity="warning",
                field_name="id_number",
            )
        )

    accepted = not any(issue.severity == "error" for issue in issues)
    score = 1.0 if accepted and not issues else 0.8 if accepted else 0.0
    return ValidationReport(accepted=accepted, score=score, issues=issues)
