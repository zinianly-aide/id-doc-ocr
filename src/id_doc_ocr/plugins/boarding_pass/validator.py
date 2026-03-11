from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


def validate_boarding_pass(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    required = [
        "flight_number",
        "ticket_number",
        "departure_date",
        "departure_airport",
        "arrival_airport",
    ]
    for field in required:
        if not fields.get(field):
            issues.append(ValidationIssue(code=f"missing_{field}", message=f"missing {field}", severity="error", field_name=field))
    if fields.get("departure_airport") and fields.get("arrival_airport") and fields["departure_airport"] == fields["arrival_airport"]:
        issues.append(ValidationIssue(code="same_departure_arrival", message="departure and arrival cannot be same", severity="error", field_name="arrival_airport"))
    accepted = not issues
    return ValidationReport(accepted=accepted, score=1.0 if accepted else 0.0, issues=issues)
