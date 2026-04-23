from __future__ import annotations

import re
from typing import Any

from id_doc_ocr.plugins.proof_common import collect_labeled_value, infer_title, normalize_date, rows_from_ocr

CERTIFICATE_NUMBER_RE = re.compile(r"([A-Z]\d{6,8}-\d{4}-\d{3,8})")
ID_NUMBER_RE = re.compile(r"\b(\d{17}[\dXx]|\d{15})\b")
TITLE_HINTS = ("结婚证",)
LABEL_ALIASES = {
    "holder_name": ["持证人", "持证人姓名"],
    "registration_date": ["登记日期", "结婚登记日期"],
    "certificate_number": ["结婚证字号", "证字号", "字号", "证号"],
    "registration_officer": ["婚姻登记员", "登记员"],
    "registration_authority": ["登记机关", "婚姻登记机关", "发证机关"],
}


def _collect_labeled_value(rows: list[str], field: str) -> str | None:
    return collect_labeled_value(rows, LABEL_ALIASES[field])



def _extract_certificate_number(value: str | None) -> str | None:
    if not value:
        return None
    compact = re.sub(r"\s+", "", value).upper()
    match = CERTIFICATE_NUMBER_RE.search(compact)
    return match.group(1) if match else compact or None



def _extract_person_blocks(rows: list[str]) -> dict[str, str | None]:
    names = [collect_labeled_value([row], ["姓名"]) for row in rows if collect_labeled_value([row], ["姓名"])]
    nationalities = [collect_labeled_value([row], ["国籍"]) for row in rows if collect_labeled_value([row], ["国籍"])]
    id_numbers: list[str] = []
    for row in rows:
        value = collect_labeled_value([row], ["身份证件号", "公民身份号码", "身份证号"])
        if not value:
            continue
        match = ID_NUMBER_RE.search(value.replace(" ", "").upper())
        id_numbers.append(match.group(1) if match else value.strip())

    return {
        "person_a_name": names[0] if len(names) > 0 else None,
        "person_a_nationality": nationalities[0] if len(nationalities) > 0 else None,
        "person_a_id_number": id_numbers[0] if len(id_numbers) > 0 else None,
        "person_b_name": names[1] if len(names) > 1 else None,
        "person_b_nationality": nationalities[1] if len(nationalities) > 1 else None,
        "person_b_id_number": id_numbers[1] if len(id_numbers) > 1 else None,
    }



def parse_marriage_certificate_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_ocr(ocr_result)
    people = _extract_person_blocks(rows)

    return {
        "doc_type": "marriage_certificate",
        "certificate_title": infer_title(rows, TITLE_HINTS),
        "holder_name": _collect_labeled_value(rows, "holder_name"),
        "registration_date": normalize_date(_collect_labeled_value(rows, "registration_date")),
        "certificate_number": _extract_certificate_number(_collect_labeled_value(rows, "certificate_number")),
        "registration_officer": _collect_labeled_value(rows, "registration_officer"),
        "registration_authority": _collect_labeled_value(rows, "registration_authority"),
        **people,
    }
