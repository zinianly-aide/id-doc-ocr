from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


def validate_medical_record(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    if not fields.get("patient_name"):
        issues.append(ValidationIssue(code="missing_patient_name", message="missing patient name", severity="error", field_name="patient_name"))
    if not fields.get("visit_date"):
        issues.append(ValidationIssue(code="missing_visit_date", message="missing visit date", severity="warning", field_name="visit_date"))

    sick_note_check = fields.get("sick_note_check") or {}
    if sick_note_check:
        if not sick_note_check.get("is_sick_note_like", False):
            issues.append(
                ValidationIssue(
                    code="not_sick_note_like",
                    message="ocr content does not strongly match sick-note characteristics",
                    severity="warning",
                    field_name="sick_note_check",
                )
            )
        if sick_note_check.get("score", 0.0) < 0.4:
            issues.append(
                ValidationIssue(
                    code="weak_sick_note_signal",
                    message="sick-note characteristic score is weak",
                    severity="info",
                    field_name="sick_note_check",
                )
            )

    accepted = not any(i.severity == "error" for i in issues)
    score = 1.0 if accepted else 0.5
    if sick_note_check:
        score = round((score + float(sick_note_check.get("score", 0.0))) / 2, 3)
    return ValidationReport(accepted=accepted, score=score, issues=issues)
