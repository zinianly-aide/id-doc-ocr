from __future__ import annotations

import re
from typing import Any

from id_doc_ocr.plugins.proof_common import collect_labeled_value, normalize_date, normalize_gender, rows_from_ocr

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


def _collect_labeled_value(rows: list[str], field: str) -> str | None:
    return collect_labeled_value(rows, LABEL_ALIASES[field])


def _normalize_time(value: str | None) -> str | None:
    if not value:
        return None
    match = TIME_RE.search(value.replace("时", ":").replace("分", ""))
    if not match:
        return None
    hh, mm = match.groups()
    return f"{int(hh):02d}:{int(mm):02d}"


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
    rows = rows_from_ocr(ocr_result)

    child_name = _collect_labeled_value(rows, "child_name")
    sex = normalize_gender(_collect_labeled_value(rows, "sex"))
    date_of_birth = normalize_date(_collect_labeled_value(rows, "date_of_birth"))
    time_of_birth = _normalize_time(_collect_labeled_value(rows, "time_of_birth"))
    gestational_weeks = _extract_int(_collect_labeled_value(rows, "gestational_weeks"), WEEKS_RE)
    birth_weight_grams = _extract_int(_collect_labeled_value(rows, "birth_weight_grams"), WEIGHT_RE)
    birth_place = _collect_labeled_value(rows, "birth_place")
    issuing_unit = _collect_labeled_value(rows, "issuing_unit")
    certificate_number = _extract_certificate_number(_collect_labeled_value(rows, "certificate_number"))
    mother_name = _collect_labeled_value(rows, "mother_name")
    mother_age = _extract_int(_collect_labeled_value(rows, "mother_age"), AGE_RE)
    father_name = _collect_labeled_value(rows, "father_name")
    issue_date = normalize_date(_collect_labeled_value(rows, "issue_date"))

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
