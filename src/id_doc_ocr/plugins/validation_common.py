from __future__ import annotations

from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


def add_missing_required_fields(
    issues: list[ValidationIssue],
    fields: dict,
    required_fields: list[str] | tuple[str, ...],
) -> None:
    for field in required_fields:
        if not fields.get(field):
            issues.append(
                ValidationIssue(
                    code=f"missing_{field}",
                    message=f"missing {field}",
                    severity="error",
                    field_name=field,
                )
            )


def finalize_validation_report(
    issues: list[ValidationIssue],
    *,
    warning_only_score: float = 0.85,
    clean_score: float = 1.0,
    rejected_score: float = 0.0,
) -> ValidationReport:
    accepted = not any(issue.severity == "error" for issue in issues)
    score = clean_score if not issues else warning_only_score if accepted else rejected_score
    return ValidationReport(accepted=accepted, score=score, issues=issues)
