from __future__ import annotations

import re
from typing import Any


ID_NUMBER_RE = re.compile(r"\d{17}[0-9Xx]")
DATE_RANGE_RE = re.compile(r"(\d{4}\.\d{2}\.\d{2}|\d{8})\s*[-—一至]\s*(长期|\d{4}\.\d{2}\.\d{2}|\d{8})")
COMPACT_LABELS = {
    "姓名": "name",
    "出生": "birth_date",
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


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _extract_compact_value(compact_lines: list[str], label: str) -> str | None:
    for line in compact_lines:
        if label not in line:
            continue
        value = line.split(label, 1)[1].strip(" :：")
        if value:
            return value
    return None


def parse_china_id_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(ocr_result)
    compact_lines = [_compact(row) for row in rows]
    joined = "\n".join(rows)

    is_back = any(token in joined for token in ["签发机关", "有效期限"]) and "公民身份号码" not in joined
    fields: dict[str, Any] = {
        "document_side": "back" if is_back else "front",
        "name": None,
        "gender": None,
        "ethnicity": None,
        "birth_date": None,
        "address": None,
        "id_number": None,
        "issuing_authority": None,
        "valid_from": None,
        "valid_to": None,
    }

    if not is_back:
        for label, field_name in COMPACT_LABELS.items():
            value = _extract_compact_value(compact_lines, label)
            if value:
                fields[field_name] = value

        for line in compact_lines:
            gender_match = re.search(r"性别([男女])", line)
            if gender_match:
                fields["gender"] = gender_match.group(1)
            ethnicity_match = re.search(r"民族([\u4e00-\u9fa5]{1,4})", line)
            if ethnicity_match:
                fields["ethnicity"] = ethnicity_match.group(1)

        address_chunks: list[str] = []
        collecting_address = False
        for line in compact_lines:
            if "住址" in line:
                collecting_address = True
                remainder = line.split("住址", 1)[1].strip(" :：")
                if remainder:
                    address_chunks.append(remainder)
                continue
            if collecting_address:
                if "公民身份号码" in line or "身份证号码" in line:
                    break
                if line in {"姓名", "性别", "民族", "出生"}:
                    continue
                address_chunks.append(line)
        if address_chunks:
            fields["address"] = "".join(address_chunks)

        for line in compact_lines:
            match = ID_NUMBER_RE.search(line)
            if match:
                fields["id_number"] = match.group(0).upper()
                break
    else:
        issuing_authority = _extract_compact_value(compact_lines, "签发机关")
        if issuing_authority:
            fields["issuing_authority"] = issuing_authority

        for line in compact_lines:
            match = DATE_RANGE_RE.search(line)
            if match:
                fields["valid_from"] = match.group(1)
                fields["valid_to"] = match.group(2)
                break
            if "有效期限" in line:
                value = line.split("有效期限", 1)[1].strip(" :：")
                if value:
                    parts = re.split(r"[-—一至]", value, maxsplit=1)
                    if parts:
                        fields["valid_from"] = parts[0]
                    if len(parts) > 1:
                        fields["valid_to"] = parts[1]

    return fields
