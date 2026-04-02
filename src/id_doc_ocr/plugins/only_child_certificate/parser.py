from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"(20\d{2}|19\d{2})[年\-/.](\d{1,2})[月\-/.](\d{1,2})日?")
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


def _rows(ocr_result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for item in ocr_result.get("lines", []):
        text = str(item.get("text") or "").strip()
        if text:
            rows.append(text)
    if not rows and ocr_result.get("text"):
        rows.extend(line.strip() for line in str(ocr_result["text"]).splitlines() if line.strip())
    return rows


def _normalize_text(text: str) -> str:
    return text.replace("：", ":").replace("（", "(").replace("）", ")").strip()


def _after_label(text: str, aliases: list[str]) -> str | None:
    normalized = _normalize_text(text)
    upper = normalized.upper()
    for alias in aliases:
        alias_upper = alias.upper()
        if upper.startswith(alias_upper + ":"):
            return normalized[len(alias) + 1 :].strip()
        if upper == alias_upper:
            return ""
    return None


def _collect_labeled_value(rows: list[str], field: str) -> str | None:
    aliases = LABEL_ALIASES[field]
    for idx, row in enumerate(rows):
        value = _after_label(row, aliases)
        if value is None:
            continue
        if value:
            return value
        if idx + 1 < len(rows):
            candidate = rows[idx + 1].strip()
            if candidate:
                return candidate
    return None


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _normalize_gender(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.strip().upper()
    if "男" in value or compact == "MALE":
        return "男"
    if "女" in value or compact == "FEMALE":
        return "女"
    return value.strip()


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
    rows = _rows(ocr_result)

    return {
        "doc_type": "only_child_certificate",
        "certificate_title": _infer_title(rows),
        "certificate_number": _normalize_certificate_number(_collect_labeled_value(rows, "certificate_number")),
        "child_name": _collect_labeled_value(rows, "child_name"),
        "child_gender": _normalize_gender(_collect_labeled_value(rows, "child_gender")),
        "child_birth_date": _normalize_date(_collect_labeled_value(rows, "child_birth_date")),
        "father_name": _collect_labeled_value(rows, "father_name"),
        "mother_name": _collect_labeled_value(rows, "mother_name"),
        "issue_date": _normalize_date(_collect_labeled_value(rows, "issue_date")),
        "issuing_authority": _collect_labeled_value(rows, "issuing_authority"),
        "holder_address": _collect_labeled_value(rows, "holder_address"),
        "remarks": _collect_labeled_value(rows, "remarks"),
    }
