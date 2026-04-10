from __future__ import annotations

import re
from typing import Any

from id_doc_ocr.plugins.proof_common import (
    collect_labeled_value,
    normalize_date,
    normalize_gender,
    rows_from_ocr,
)

CERT_NO_RE = re.compile(r"([沪苏浙皖赣]?[A-Z]?\d{5,20})")
LABEL_ALIASES = {
    "certificate_number": ["证号", "编号", "证件编号", "独生子女父母光荣证号"],
    "child_name": ["孩子姓名", "子女姓名", "独生子女姓名", "姓名"],
    "child_gender": ["子女性别", "性别"],
    "child_birth_date": ["出生日期", "出生年月", "出生年月日"],
    "father_name": ["父亲姓名", "父亲"],
    "mother_name": ["母亲姓名", "母亲"],
    "issue_date": ["发证日期", "领证日期", "签发日期"],
    "issuing_authority": ["发证机关", "发证单位", "发证机构", "签发机关"],
    "holder_address": ["家庭住址", "住址", "现住址"],
    "remarks": ["备注", "说明"],
}
TITLE_HINTS = ("独生子女父母光荣证", "独生子女证")


def _collect_labeled_value(rows: list[str], field: str) -> str | None:
    return collect_labeled_value(rows, LABEL_ALIASES[field])


def _normalize_certificate_number(value: str | None) -> str | None:
    if not value:
        return None
    compact = re.sub(r"\s+", "", value).upper()
    match = CERT_NO_RE.search(compact)
    return match.group(1) if match else compact or None


def _infer_title(rows: list[str]) -> str | None:
    for row in rows[:3]:
        if any(hint in row for hint in TITLE_HINTS):
            return row.strip()
    return None


def parse_only_child_certificate_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_ocr(ocr_result)

    return {
        "doc_type": "only_child_certificate",
        "certificate_title": _infer_title(rows),
        "certificate_number": _normalize_certificate_number(_collect_labeled_value(rows, "certificate_number")),
        "child_name": _collect_labeled_value(rows, "child_name"),
        "child_gender": normalize_gender(_collect_labeled_value(rows, "child_gender")),
        "child_birth_date": normalize_date(_collect_labeled_value(rows, "child_birth_date")),
        "father_name": _collect_labeled_value(rows, "father_name"),
        "mother_name": _collect_labeled_value(rows, "mother_name"),
        "issue_date": normalize_date(_collect_labeled_value(rows, "issue_date")),
        "issuing_authority": _collect_labeled_value(rows, "issuing_authority"),
        "holder_address": _collect_labeled_value(rows, "holder_address"),
        "remarks": _collect_labeled_value(rows, "remarks"),
    }
