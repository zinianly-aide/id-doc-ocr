from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport
from id_doc_ocr.validator.china_id import validate_china_id_number


def validate_hukou_booklet(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    id_number = fields.get("id_number")
    if id_number:
        for code in validate_china_id_number(id_number):
            issues.append(ValidationIssue(code=code, message=code.replace("_", " "), severity="error", field_name="id_number"))
    accepted = not issues
    return ValidationReport(accepted=accepted, score=1.0 if accepted else 0.0, issues=issues)
