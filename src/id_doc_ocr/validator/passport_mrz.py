from id_doc_ocr.parsers.mrz import parse_td3, validate_td3
from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


def build_passport_mrz_report(lines: list[str]) -> ValidationReport:
    try:
        parsed = parse_td3(lines)
    except Exception as e:
        return ValidationReport(
            accepted=False,
            score=0.0,
            issues=[ValidationIssue(code="mrz_parse_failed", message=str(e), severity="error", field_name="mrz")],
        )

    raw_issues = validate_td3(parsed)
    issues = [
        ValidationIssue(code=code, message=code.replace("_", " "), severity="error", field_name="mrz")
        for code in raw_issues
    ]
    return ValidationReport(accepted=not issues, score=1.0 if not issues else 0.0, issues=issues)
