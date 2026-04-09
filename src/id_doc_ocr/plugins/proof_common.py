from __future__ import annotations

import re
from typing import Any

DATE_RE = re.compile(r"(20\d{2}|19\d{2})[年\-/.](\d{1,2})[月\-/.](\d{1,2})日?")
GENDER_TOKENS = {"男": "男", "女": "女", "MALE": "男", "FEMALE": "女"}
ID_NUMBER_RE = re.compile(r"\b(\d{17}[\dXx]|\d{15})\b")


def rows_from_ocr(ocr_result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for item in ocr_result.get("lines", []):
        text = str(item.get("text") or "").strip()
        if text:
            rows.append(text)
    if not rows and ocr_result.get("text"):
        rows.extend(line.strip() for line in str(ocr_result["text"]).splitlines() if line.strip())
    return rows


def normalize_label_text(text: str) -> str:
    return (
        text.replace("：", ":")
        .replace("（", "(")
        .replace("）", ")")
        .replace(" ", " ")
        .strip()
    )


def after_label(text: str, aliases: list[str]) -> str | None:
    normalized = normalize_label_text(text)
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


def normalize_gender(value: str | None) -> str | None:
    if not value:
        return None
    upper = value.upper()
    for token, normalized in GENDER_TOKENS.items():
        if token in upper or token in value:
            return normalized
    return value.strip()


def collect_field_value(rows: list[str], aliases_by_field: dict[str, list[str]], field: str) -> str | None:
    return collect_labeled_value(rows, aliases_by_field[field])


def infer_title(rows: list[str], title_hints: tuple[str, ...], *, limit: int = 5, requires_keyword: str | None = None) -> str | None:
    for row in rows[:limit]:
        if requires_keyword and requires_keyword not in row:
            continue
        if any(hint in row for hint in title_hints):
            return row.strip()
    return None


def extract_id_number(value: str | None) -> str | None:
    if not value:
        return None
    compact = re.sub(r"\s+", "", value).upper()
    match = ID_NUMBER_RE.search(compact)
    return match.group(1) if match else None
