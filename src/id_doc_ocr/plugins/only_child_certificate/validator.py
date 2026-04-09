from __future__ import annotations

import re

from id_doc_ocr.plugins.validation_common import add_missing_required_fields, finalize_validation_report
from id_doc_ocr.schemas.types import ValidationIssue, ValidationReport


VALID_GENDER = {"男", "女"}
CERTIFICATE_NUMBER_RE = re.compile(r"^[沪苏浙皖赣]?[A-Z]?\d{5,20}$")
EAST_CHINA_HINTS = (
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "江西",
    "浦东",
    "黄浦",
    "徐汇",
    "静安",
    "闵行",
    "苏州",
    "杭州",
    "宁波",
    "南京",
    "合肥",
)
TITLE_HINTS = ("独生子女父母光荣证", "独生子女证")


def validate_only_child_certificate(fields: dict) -> ValidationReport:
    issues: list[ValidationIssue] = []

    add_missing_required_fields(issues, fields, ["child_name", "child_birth_date", "father_name", "mother_name"])

    certificate_title = fields.get("certificate_title")
    if certificate_title and not any(hint in certificate_title for hint in TITLE_HINTS):
        issues.append(
            ValidationIssue(
                code="certificate_title_suspect",
                message="certificate title does not look like only-child certificate",
                severity="warning",
                field_name="certificate_title",
            )
        )

    child_gender = fields.get("child_gender")
    if child_gender and child_gender not in VALID_GENDER:
        issues.append(
            ValidationIssue(
                code="invalid_child_gender",
                message="invalid child gender",
                severity="error",
                field_name="child_gender",
            )
        )

    certificate_number = fields.get("certificate_number")
    if certificate_number and not CERTIFICATE_NUMBER_RE.match(str(certificate_number).strip().upper()):
        issues.append(
            ValidationIssue(
                code="certificate_number_format_suspect",
                message="certificate number format suspect",
                severity="warning",
                field_name="certificate_number",
            )
        )

    regional_text = " ".join(
        part for part in [fields.get("issuing_authority") or "", fields.get("holder_address") or ""] if part
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

    return finalize_validation_report(issues)
