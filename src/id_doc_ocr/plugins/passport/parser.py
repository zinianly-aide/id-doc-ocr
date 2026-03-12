from __future__ import annotations

import re
from typing import Any

from id_doc_ocr.parsers.mrz import parse_td3


MRZ_ALLOWED_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")


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


def _normalize_mrz_line(text: str) -> str:
    text = re.sub(r"\s+", "", text.upper())
    text = text.replace("«", "<")
    return text


def _looks_like_td3_line(text: str) -> bool:
    normalized = _normalize_mrz_line(text)
    return len(normalized) == 44 and set(normalized) <= MRZ_ALLOWED_CHARS


def extract_td3_mrz_lines(ocr_result: dict[str, Any]) -> list[str]:
    candidates = [_normalize_mrz_line(row) for row in _rows(ocr_result) if _looks_like_td3_line(row)]
    for idx in range(len(candidates) - 1):
        if candidates[idx].startswith("P<"):
            return [candidates[idx], candidates[idx + 1]]
    return candidates[:2] if len(candidates) >= 2 else []


def _format_mrz_date(value: str) -> str | None:
    if len(value) != 6 or not value.isdigit():
        return None
    yy = int(value[:2])
    mm = value[2:4]
    dd = value[4:6]
    century = 1900 if yy >= 50 else 2000
    return f"{century + yy:04d}-{mm}-{dd}"


def parse_passport_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "document_variant": "passport",
        "mrz_lines": [],
        "mrz_fields": {},
        "document_code": None,
        "issuing_country": None,
        "surname": None,
        "given_names": None,
        "passport_number": None,
        "nationality": None,
        "birth_date": None,
        "sex": None,
        "expiry_date": None,
        "personal_number": None,
    }

    mrz_lines = extract_td3_mrz_lines(ocr_result)
    fields["mrz_lines"] = mrz_lines
    if len(mrz_lines) != 2:
        return fields

    parsed = parse_td3(mrz_lines)
    normalized_fields = {
        "document_code": parsed.document_code,
        "issuing_country": parsed.issuing_country,
        "surname": parsed.surname,
        "given_names": parsed.given_names,
        "passport_number": parsed.passport_number.replace("<", ""),
        "nationality": parsed.nationality,
        "birth_date": _format_mrz_date(parsed.birth_date),
        "sex": parsed.sex if parsed.sex != "<" else None,
        "expiry_date": _format_mrz_date(parsed.expiry_date),
        "personal_number": parsed.personal_number.rstrip("<") or None,
    }
    fields["mrz_fields"] = normalized_fields.copy()
    fields.update(normalized_fields)
    return fields
