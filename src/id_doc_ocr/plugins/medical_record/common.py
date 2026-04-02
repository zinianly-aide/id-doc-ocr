from __future__ import annotations

import re
from typing import Any

DATE_RE = re.compile(r"\b(19\d{2}|20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})日?\b")
AGE_RE = re.compile(r"(\d{1,3})\s*岁")
GENDER_TOKENS = {"男": "男", "女": "女", "MALE": "男", "FEMALE": "女"}


def rows_from_ocr(ocr_result: dict[str, Any]) -> list[str]:
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


def after_label(text: str, aliases: list[str]) -> str | None:
    normalized = text.replace("：", ":")
    upper = normalized.upper()
    for alias in aliases:
        alias_upper = alias.upper()
        if upper.startswith(alias_upper + ":"):
            return normalized[len(alias) + 1 :].strip()
        if upper == alias_upper:
            return ""
    return None


def collect_labeled_value(rows: list[str], aliases: list[str]) -> str | None:
    for idx, row in enumerate(rows):
        value = after_label(row, aliases)
        if value is None:
            continue
        if value:
            return value
        if idx + 1 < len(rows):
            candidate = rows[idx + 1].strip()
            if candidate:
                return candidate
    return None


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def find_all_dates(text: str) -> list[str]:
    return [
        f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        for year, month, day in DATE_RE.findall(text)
    ]


def normalize_gender(value: str | None) -> str | None:
    if not value:
        return None
    upper = value.upper()
    for token, normalized in GENDER_TOKENS.items():
        if token in upper or token in value:
            return normalized
    return value.strip()


def normalize_age(value: str | None) -> str | None:
    if not value:
        return None
    match = AGE_RE.search(value)
    if match:
        return match.group(1)
    digits = re.findall(r"\d+", value)
    return digits[0] if digits else value.strip()


def split_items(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[；;、,，]\s*", value)
    return [part.strip() for part in parts if part.strip()]
