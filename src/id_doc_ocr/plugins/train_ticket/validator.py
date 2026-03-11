from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


def validate_train_ticket(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    required = [
        "ticket_number",
        "train_number",
        "departure_station",
        "arrival_station",
        "departure_time",
    ]
    for field in required:
        if not fields.get(field):
            issues.append(ValidationIssue(code=f"missing_{field}", message=f"missing {field}", severity="error", field_name=field))
    accepted = not issues
    return ValidationReport(accepted=accepted, score=1.0 if accepted else 0.0, issues=issues)
