from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


def validate_medical_record(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    if not fields.get("patient_name"):
        issues.append(ValidationIssue(code="missing_patient_name", message="missing patient name", severity="error", field_name="patient_name"))
    if not fields.get("visit_date"):
        issues.append(ValidationIssue(code="missing_visit_date", message="missing visit date", severity="warning", field_name="visit_date"))
    accepted = not any(i.severity == "error" for i in issues)
    return ValidationReport(accepted=accepted, score=1.0 if accepted else 0.5, issues=issues)
