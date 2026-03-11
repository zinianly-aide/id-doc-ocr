from __future__ import annotations

from datetime import datetime

from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


CN_ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
CN_ID_CODES = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]


def validate_china_id_number(id_number: str) -> list[str]:
    issues: list[str] = []
    if len(id_number) != 18:
        return ["length_invalid"]
    if not id_number[:17].isdigit() or not (id_number[-1].isdigit() or id_number[-1].upper() == "X"):
        return ["format_invalid"]

    birth = id_number[6:14]
    try:
        datetime.strptime(birth, "%Y%m%d")
    except ValueError:
        issues.append("birth_date_invalid")

    total = sum(int(n) * w for n, w in zip(id_number[:17], CN_ID_WEIGHTS))
    expected = CN_ID_CODES[total % 11]
    if id_number[-1].upper() != expected:
        issues.append("checksum_invalid")
    return issues


def build_china_id_validation_report(id_number: str | None) -> ValidationReport:
    issues: list[ValidationIssue] = []
    accepted = True
    if not id_number:
        accepted = False
        issues.append(ValidationIssue(code="missing_id_number", message="ID number is missing", severity="error", field_name="id_number"))
    else:
        raw_issues = validate_china_id_number(id_number)
        for code in raw_issues:
            accepted = False
            issues.append(ValidationIssue(code=code, message=code.replace("_", " "), severity="error", field_name="id_number"))
    return ValidationReport(accepted=accepted, score=1.0 if accepted else 0.0, issues=issues)
