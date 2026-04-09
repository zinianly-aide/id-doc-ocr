from __future__ import annotations

from id_doc_ocr.plugins.validation_common import add_missing_required_fields, finalize_validation_report
from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


REQUIRED_FIELDS = ["hospital_name", "diagnosis", "issue_date"]


def validate_diagnosis_proof(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []

    add_missing_required_fields(issues, fields, REQUIRED_FIELDS)

    if not fields.get("certificate_title"):
        issues.append(
            ValidationIssue(
                code="missing_certificate_title",
                message="missing diagnosis certificate title",
                severity="warning",
                field_name="certificate_title",
            )
        )

    if not fields.get("advice"):
        issues.append(
            ValidationIssue(
                code="missing_advice",
                message="missing advice / treatment suggestion",
                severity="warning",
                field_name="advice",
            )
        )

    if not fields.get("physician_name"):
        issues.append(
            ValidationIssue(
                code="missing_physician_name",
                message="missing physician name/signature",
                severity="warning",
                field_name="physician_name",
            )
        )

    if not fields.get("department") and not fields.get("physician_department"):
        issues.append(
            ValidationIssue(
                code="missing_department",
                message="missing department",
                severity="warning",
                field_name="department",
            )
        )

    if not fields.get("seal_present"):
        issues.append(
            ValidationIssue(
                code="missing_seal",
                message="missing visible hospital/diagnosis seal",
                severity="warning",
                field_name="seal_present",
            )
        )

    rest_start_date = fields.get("rest_start_date")
    rest_end_date = fields.get("rest_end_date")
    if bool(rest_start_date) != bool(rest_end_date):
        issues.append(
            ValidationIssue(
                code="rest_date_range_incomplete",
                message="rest date range is incomplete",
                severity="warning",
                field_name="rest_start_date",
            )
        )

    return finalize_validation_report(issues)
