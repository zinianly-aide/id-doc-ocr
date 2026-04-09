from __future__ import annotations

import re

from id_doc_ocr.plugins.validation_common import add_missing_required_fields, finalize_validation_report
from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


EAST_CHINA_HINTS = (
    "上海",
    "浦东",
    "黄浦",
    "徐汇",
    "静安",
    "闵行",
    "宝山",
    "嘉定",
    "松江",
    "青浦",
    "江苏",
    "苏州",
    "南京",
    "无锡",
    "浙江",
    "杭州",
    "宁波",
    "嘉兴",
    "安徽",
    "合肥",
    "芜湖",
)
TITLE_HINTS = ("抚养关系证明", "监护关系证明", "关系证明", "情况证明")
RELATION_HINT_RE = re.compile(r"父子|父女|母子|母女|祖孙|外祖孙|监护|抚养")
AUTHORITY_FEATURE_HINTS = {
    "residents_committee",
    "village_committee",
    "subdistrict_office",
    "police_station",
    "town_government",
    "civil_affairs",
    "community_service_center",
}
ID_RE = re.compile(r"^(\d{17}[\dXx]|\d{15})$")


def validate_custody_relationship_certificate(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []

    add_missing_required_fields(issues, fields, ["child_name", "guardian_name", "issuing_authority"])

    relation = fields.get("relation")
    relation_statement = fields.get("relation_statement")
    relation_text = " ".join(part for part in [relation or "", relation_statement or ""] if part)
    if not relation_text:
        issues.append(
            ValidationIssue(
                code="missing_relation_signal",
                message="missing relation or custody statement",
                severity="error",
                field_name="relation",
            )
        )
    elif not RELATION_HINT_RE.search(relation_text):
        issues.append(
            ValidationIssue(
                code="weak_relation_signal",
                message="relation text does not look like custody/guardianship wording",
                severity="warning",
                field_name="relation",
            )
        )

    certificate_title = fields.get("certificate_title")
    if certificate_title and not any(hint in certificate_title for hint in TITLE_HINTS):
        issues.append(
            ValidationIssue(
                code="certificate_title_suspect",
                message="certificate title does not look like custody/guardianship proof",
                severity="warning",
                field_name="certificate_title",
            )
        )

    for field in ["child_id_number", "guardian_id_number"]:
        value = fields.get(field)
        if value and not ID_RE.match(str(value).strip()):
            issues.append(
                ValidationIssue(
                    code=f"{field}_format_suspect",
                    message=f"{field} format suspect",
                    severity="warning",
                    field_name=field,
                )
            )

    authority_features = set(fields.get("authority_features") or [])
    if not authority_features:
        issues.append(
            ValidationIssue(
                code="missing_authority_feature",
                message="issuing authority lacks recognizable grassroots/government feature",
                severity="warning",
                field_name="issuing_authority",
            )
        )
    elif not (authority_features & AUTHORITY_FEATURE_HINTS):
        issues.append(
            ValidationIssue(
                code="authority_feature_unrecognized",
                message="authority features are present but not in expected custody-proof set",
                severity="warning",
                field_name="issuing_authority",
            )
        )

    regional_text = " ".join(
        part
        for part in [fields.get("issuing_authority") or "", fields.get("subject_address") or "", fields.get("purpose") or ""]
        if part
    )
    if regional_text and not any(hint in regional_text for hint in EAST_CHINA_HINTS):
        issues.append(
            ValidationIssue(
                code="not_east_china_style",
                message="document lacks Shanghai/East-China regional hints",
                severity="warning",
                field_name="issuing_authority",
            )
        )

    if not fields.get("issue_date"):
        issues.append(
            ValidationIssue(
                code="missing_issue_date",
                message="issue date missing from proof text",
                severity="warning",
                field_name="issue_date",
            )
        )

    return finalize_validation_report(issues)
