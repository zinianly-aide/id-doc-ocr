from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"(20\d{2}|19\d{2})[年\-/.](\d{1,2})[月\-/.](\d{1,2})日?")
TIME_RE = re.compile(r"\b([01]?\d|2[0-3])[:：]([0-5]\d)\b")
WEEKS_RE = re.compile(r"(\d{2})\s*周")
WEIGHT_RE = re.compile(r"(\d{3,4})\s*(?:克|g|G)\b")
AGE_RE = re.compile(r"(\d{1,2})\s*岁")
CERT_RE = re.compile(r"\b([A-Z]{1,2}\d{8,10})\b")
LABEL_ALIASES = {
    "child_name": ["新生儿姓名", "姓名", "婴儿姓名"],
    "sex": ["性别"],
    "date_of_birth": ["出生日期", "出生年月日"],
    "time_of_birth": ["出生时间"],
    "gestational_weeks": ["孕周", "孕龄"],
    "birth_weight_grams": ["出生体重", "体重"],
    "birth_place": ["出生地点", "出生地"],
    "issuing_unit": ["签发机构", "签发单位", "出生机构", "分娩机构"],
    "certificate_number": ["出生医学证明编号", "证件编号", "证号"],
    "mother_name": ["母亲姓名", "产妇姓名"],
    "mother_age": ["母亲年龄", "产妇年龄"],
    "father_name": ["父亲姓名"],
    "issue_date": ["签发日期", "发证日期"],
}


def _rows(ocr_result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for item in ocr_result.get("lines", []):
        text = str(item.get("text") or "").strip()
        if text:
            rows.append(text)
    if not rows and ocr_result.get("text"):
        rows.extend(line.strip() for line in str(ocr_result["text"]).splitlines() if line.strip())
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
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _normalize_time(value: str | None) -> str | None:
    if not value:
        return None
    match = TIME_RE.search(value.replace("时", ":").replace("分", ""))
    if not match:
        return None
    hh, mm = match.groups()
    return f"{int(hh):02d}:{int(mm):02d}"


def _normalize_sex(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().upper()
    if "男" in value or normalized == "MALE":
        return "男"
    if "女" in value or normalized == "FEMALE":
        return "女"
    return value.strip()


def _extract_int(value: str | None, pattern: re.Pattern[str]) -> int | None:
    if not value:
        return None
    match = pattern.search(value)
    return int(match.group(1)) if match else None


def _extract_certificate_number(value: str | None) -> str | None:
    if not value:
        return None
    compact = re.sub(r"\s+", "", value).upper()
    match = CERT_RE.search(compact)
    return match.group(1) if match else compact or None


def parse_birth_certificate_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(ocr_result)

    child_name = _collect_labeled_value(rows, "child_name")
    sex = _normalize_sex(_collect_labeled_value(rows, "sex"))
    date_of_birth = _normalize_date(_collect_labeled_value(rows, "date_of_birth"))
    time_of_birth = _normalize_time(_collect_labeled_value(rows, "time_of_birth"))
    gestational_weeks = _extract_int(_collect_labeled_value(rows, "gestational_weeks"), WEEKS_RE)
    birth_weight_grams = _extract_int(_collect_labeled_value(rows, "birth_weight_grams"), WEIGHT_RE)
    birth_place = _collect_labeled_value(rows, "birth_place")
    issuing_unit = _collect_labeled_value(rows, "issuing_unit")
    certificate_number = _extract_certificate_number(_collect_labeled_value(rows, "certificate_number"))
    mother_name = _collect_labeled_value(rows, "mother_name")
    mother_age = _extract_int(_collect_labeled_value(rows, "mother_age"), AGE_RE)
    father_name = _collect_labeled_value(rows, "father_name")
    issue_date = _normalize_date(_collect_labeled_value(rows, "issue_date"))

    return {
        "doc_type": "birth_certificate",
        "child_name": child_name,
        "sex": sex,
        "date_of_birth": date_of_birth,
        "time_of_birth": time_of_birth,
        "gestational_weeks": gestational_weeks,
        "birth_weight_grams": birth_weight_grams,
        "birth_place": birth_place,
        "issuing_unit": issuing_unit,
        "certificate_number": certificate_number,
        "mother_name": mother_name,
        "mother_age": mother_age,
        "father_name": father_name,
        "issue_date": issue_date,
    }
