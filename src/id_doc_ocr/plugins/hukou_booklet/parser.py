from __future__ import annotations

import re
from datetime import datetime
from typing import Any


DATE_RE = re.compile(r"\b\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?\b")
HOUSEHOLD_ID_RE = re.compile(r"\d{6,12}")
ID_RE = re.compile(r"\d{17}[\dXx]")
GENDER_TOKENS = {"男": "男", "女": "女", "MALE": "男", "FEMALE": "女"}
LABEL_ALIASES = {
    "household_id": ["户号", "HOUSEHOLD ID"],
    "householder_name": ["户主姓名", "户主", "HOUSEHOLDER", "HEAD OF HOUSEHOLD"],
    "address": ["住址", "ADDRESS"],
    "member_name": ["姓名", "成员姓名", "NAME"],
    "relation_to_head": ["与户主关系", "关系", "RELATIONSHIP"],
    "gender": ["性别", "SEX", "GENDER"],
    "birth_date": ["出生日期", "出生年月日", "BIRTH DATE", "DATE OF BIRTH"],
    "id_number": ["公民身份号码", "身份证号", "身份证号码", "ID NUMBER"],
}


def _rows(ocr_result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for item in ocr_result.get("lines", []):
        text = (item.get("text") or "").strip()
        if text:
            rows.append(text)
    if not rows and ocr_result.get("text"):
        for line in str(ocr_result["text"]).splitlines():
            line = line.strip()
            if line:
                rows.append(line)
    return rows


def _after_label(text: str, aliases: list[str]) -> str | None:
    normalized = text.replace("：", ":")
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
    m = DATE_RE.search(value)
    if not m:
        return None
    date_text = m.group(0).replace("年", "-").replace("月", "-").replace("日", "")
    date_text = date_text.replace("/", "-").replace(".", "-")
    parts = [p for p in date_text.split("-") if p]
    if len(parts) != 3:
        return date_text
    yyyy, mm, dd = parts
    try:
        return f"{int(yyyy):04d}-{int(mm):02d}-{int(dd):02d}"
    except ValueError:
        return date_text


def _normalize_gender(value: str | None) -> str | None:
    if not value:
        return None
    normalized_value = value.strip()
    upper = normalized_value.upper()
    if "FEMALE" in upper or normalized_value == "女":
        return "女"
    if "MALE" in upper or normalized_value == "男":
        return "男"
    return normalized_value


def _extract_digits(value: str | None, pattern: re.Pattern[str]) -> str | None:
    if not value:
        return None
    m = pattern.search(value.replace(" ", ""))
    return m.group(0).upper() if m else value.strip()


def _infer_household_id(rows: list[str]) -> str | None:
    for row in rows:
        if "户号" in row:
            matched = _extract_digits(row, HOUSEHOLD_ID_RE)
            if matched:
                return matched
    return None


def _infer_address(rows: list[str]) -> str | None:
    for idx, row in enumerate(rows):
        if row.startswith("住址") and "：" not in row and ":" not in row and idx + 1 < len(rows):
            candidate = rows[idx + 1].strip()
            if candidate:
                return candidate
    return None


def _infer_birth_from_id(id_number: str | None) -> str | None:
    if not id_number or len(id_number) != 18 or not id_number[:17].isdigit():
        return None
    raw = id_number[6:14]
    try:
        return datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_hukou_booklet_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(ocr_result)

    household_id = _extract_digits(_collect_labeled_value(rows, "household_id"), HOUSEHOLD_ID_RE) or _infer_household_id(rows)
    householder_name = _collect_labeled_value(rows, "householder_name")
    address = _collect_labeled_value(rows, "address") or _infer_address(rows)
    member_name = _collect_labeled_value(rows, "member_name")
    relation_to_head = _collect_labeled_value(rows, "relation_to_head")
    gender = _normalize_gender(_collect_labeled_value(rows, "gender"))
    id_number = _extract_digits(_collect_labeled_value(rows, "id_number"), ID_RE)
    birth_date = _normalize_date(_collect_labeled_value(rows, "birth_date")) or _infer_birth_from_id(id_number)

    return {
        "doc_type": "hukou_booklet",
        "household_id": household_id,
        "householder_name": householder_name,
        "address": address,
        "member_name": member_name,
        "relation_to_head": relation_to_head,
        "gender": gender,
        "birth_date": birth_date,
        "id_number": id_number,
    }
