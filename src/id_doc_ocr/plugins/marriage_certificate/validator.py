from __future__ import annotations

import re

from id_doc_ocr.plugins.validation_common import add_missing_required_fields, finalize_validation_report
from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport

CERTIFICATE_NUMBER_RE = re.compile(r"^[A-Z]\d{6,8}-\d{4}-\d{3,8}$")
MARRIAGE_TITLE_HINTS = ("结婚证",)
AUTHORITY_HINTS = ("民政局", "婚姻登记处", "婚姻登记中心")
REQUIRED_FIELDS = (
    "certificate_title",
    "holder_name",
    "registration_date",
    "person_a_name",
    "person_b_name",
    "registration_authority",
)


def validate_marriage_certificate(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []

    add_missing_required_fields(issues, fields, REQUIRED_FIELDS)

    certificate_title = fields.get("certificate_title")
    if certificate_title and not any(hint in str(certificate_title) for hint in MARRIAGE_TITLE_HINTS):
        issues.append(
            ValidationIssue(
                code="certificate_title_suspect",
                message="certificate title does not look like marriage certificate",
                severity="warning",
                field_name="certificate_title",
            )
        )

    certificate_number = fields.get("certificate_number")
    if certificate_number and not CERTIFICATE_NUMBER_RE.match(str(certificate_number).strip().upper()):
        issues.append(
            ValidationIssue(
                code="certificate_number_format_suspect",
                message="certificate number format suspect",
                severity="warning",
                field_name="certificate_number",
            )
        )

    holder_name = fields.get("holder_name")
    person_names = {fields.get("person_a_name"), fields.get("person_b_name")}
    if holder_name and holder_name not in person_names:
        issues.append(
            ValidationIssue(
                code="holder_name_not_in_couple",
                message="holder name does not match either named spouse",
                severity="warning",
                field_name="holder_name",
            )
        )

    authority = str(fields.get("registration_authority") or "")
    if authority and not any(hint in authority for hint in AUTHORITY_HINTS):
        issues.append(
            ValidationIssue(
                code="registration_authority_suspect",
                message="registration authority lacks common marriage-registration hints",
                severity="warning",
                field_name="registration_authority",
            )
        )

    return finalize_validation_report(issues)
