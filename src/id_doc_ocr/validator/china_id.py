from __future__ import annotations

from datetime import datetime

from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


CN_ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
CN_ID_CODES = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]
CN_PROVINCE_CODES = {
    "11", "12", "13", "14", "15",
    "21", "22", "23",
    "31", "32", "33", "34", "35", "36", "37",
    "41", "42", "43", "44", "45", "46",
    "50", "51", "52", "53", "54",
    "61", "62", "63", "64", "65",
    "71", "81", "82",
}


def validate_china_id_number(id_number: str) -> list[str]:
    normalized = (id_number or "").strip().upper()
    issues: list[str] = []
    if len(normalized) != 18:
        return ["length_invalid"]
    if not normalized[:17].isdigit() or not (normalized[-1].isdigit() or normalized[-1] == "X"):
        return ["format_invalid"]

    if normalized[:2] not in CN_PROVINCE_CODES or normalized[:6] == "000000":
        issues.append("region_code_invalid")

    birth = normalized[6:14]
    try:
        birth_date = datetime.strptime(birth, "%Y%m%d")
        if birth_date.date() > datetime.now().date():
            issues.append("birth_date_invalid")
    except ValueError:
        issues.append("birth_date_invalid")

    total = sum(int(n) * w for n, w in zip(normalized[:17], CN_ID_WEIGHTS))
    expected = CN_ID_CODES[total % 11]
    if normalized[-1] != expected:
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
