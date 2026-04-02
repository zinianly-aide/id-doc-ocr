from __future__ import annotations

import re
from typing import Any

from id_doc_ocr.plugins.medical_record.common import (
    collect_labeled_value,
    find_all_dates,
    normalize_age,
    normalize_date,
    normalize_gender,
    rows_from_ocr,
    split_items,
)

HOSPITAL_RE = re.compile(r"(医院|卫生院|医疗中心|门诊部|中医院|妇幼保健院)")
TITLE_RE = re.compile(r"(诊断证明书|疾病诊断证明书|诊断证明|门诊诊断证明书|诊疗证明书)")
DATE_RANGE_RE = re.compile(
    r"(?:建议|医嘱|全休|休息|病休|治疗).{0,24}?(?:自|从)?\s*((?:19|20)\d{2}[年\-/.]\d{1,2}[月\-/.]\d{1,2}日?)\s*(?:至|到)\s*((?:19|20)\d{2}[年\-/.]\d{1,2}[月\-/.]\d{1,2}日?)"
)
REST_DAYS_RE = re.compile(r"(?:休息|病休|全休|建议).{0,12}?(\d{1,2})\s*(?:天|日)")
PHYSICIAN_RE = re.compile(r"(?:医师|医生|医师签名|接诊医师|签名)[:：]?\s*([\u4e00-\u9fa5A-Za-z·]{2,20})")
SEAL_RE = re.compile(r"(诊断证明章|诊断专用章|医疗证明专用章|门诊部专用章|医院公章|盖章|印章|公章)")

LABEL_ALIASES = {
    "hospital_name": ["医院", "医院名称", "就诊医院", "医疗机构"],
    "certificate_title": ["证明名称", "标题"],
    "patient_name": ["姓名", "患者姓名"],
    "gender": ["性别"],
    "age": ["年龄"],
    "department": ["科室", "科别", "就诊科室", "门诊科室"],
    "diagnosis": ["诊断", "临床诊断", "初步诊断", "诊断意见"],
    "advice": ["建议", "医嘱", "处理意见", "治疗意见", "建议休息"],
    "issue_date": ["日期", "开具日期", "签发日期", "出具日期"],
    "physician_name": ["医师", "医生", "医师签名", "接诊医师"],
    "physician_department": ["医生科室", "医师科室", "签发科室"],
}


def _find_hospital_name(rows: list[str]) -> str | None:
    labeled = collect_labeled_value(rows, LABEL_ALIASES["hospital_name"])
    if labeled:
        return labeled
    for row in rows[:4]:
        if HOSPITAL_RE.search(row):
            return row.strip()
    return None


def _find_certificate_title(rows: list[str], joined: str) -> str | None:
    labeled = collect_labeled_value(rows, LABEL_ALIASES["certificate_title"])
    if labeled:
        return labeled
    match = TITLE_RE.search(joined)
    return match.group(0) if match else None


def _find_diagnosis(rows: list[str]) -> list[str]:
    value = collect_labeled_value(rows, LABEL_ALIASES["diagnosis"])
    if value:
        return split_items(value)
    collected: list[str] = []
    for idx, row in enumerate(rows):
        normalized = row.replace("：", ":")
        if any(normalized.startswith(alias + ":") for alias in LABEL_ALIASES["diagnosis"]):
            tail = normalized.split(":", 1)[1].strip()
            if tail:
                collected.extend(split_items(tail))
            elif idx + 1 < len(rows):
                collected.extend(split_items(rows[idx + 1]))
            break
    return collected


def _find_advice(rows: list[str]) -> list[str]:
    value = collect_labeled_value(rows, LABEL_ALIASES["advice"])
    if value:
        return split_items(value)
    advice_rows = [row for row in rows if any(token in row for token in ("建议", "医嘱", "休息", "病休", "治疗"))]
    return advice_rows[:2]


def _extract_rest_range(joined: str) -> tuple[str | None, str | None, int | None]:
    start_date = end_date = None
    match = DATE_RANGE_RE.search(joined)
    if match:
        start_date = normalize_date(match.group(1))
        end_date = normalize_date(match.group(2))
    rest_days = None
    days_match = REST_DAYS_RE.search(joined)
    if days_match:
        rest_days = int(days_match.group(1))
    return start_date, end_date, rest_days


def _find_issue_date(rows: list[str], joined: str) -> str | None:
    labeled = normalize_date(collect_labeled_value(rows, LABEL_ALIASES["issue_date"]))
    if labeled:
        return labeled
    dates = find_all_dates(joined)
    return dates[-1] if dates else None


def _find_physician_name(rows: list[str], joined: str) -> str | None:
    labeled = collect_labeled_value(rows, LABEL_ALIASES["physician_name"])
    if labeled:
        return labeled
    match = PHYSICIAN_RE.search(joined)
    return match.group(1) if match else None


def _find_seal_text(rows: list[str], joined: str) -> str | None:
    match = SEAL_RE.search(joined)
    if match:
        for row in rows[::-1]:
            if match.group(1) in row:
                return row.strip()
        return match.group(1)
    return None



def parse_diagnosis_proof_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_ocr(ocr_result)
    joined = "\n".join(rows)

    hospital_name = _find_hospital_name(rows)
    certificate_title = _find_certificate_title(rows, joined)
    patient_name = collect_labeled_value(rows, LABEL_ALIASES["patient_name"])
    gender = normalize_gender(collect_labeled_value(rows, LABEL_ALIASES["gender"]))
    age = normalize_age(collect_labeled_value(rows, LABEL_ALIASES["age"]))
    department = collect_labeled_value(rows, LABEL_ALIASES["department"])
    diagnosis = _find_diagnosis(rows)
    advice = _find_advice(rows)
    issue_date = _find_issue_date(rows, joined)
    rest_start_date, rest_end_date, rest_days = _extract_rest_range(joined)
    physician_name = _find_physician_name(rows, joined)
    physician_department = collect_labeled_value(rows, LABEL_ALIASES["physician_department"]) or department
    seal_text = _find_seal_text(rows, joined)

    return {
        "doc_type": "diagnosis_proof",
        "hospital_name": hospital_name,
        "certificate_title": certificate_title,
        "patient_name": patient_name,
        "gender": gender,
        "age": age,
        "department": department,
        "diagnosis": diagnosis,
        "advice": advice,
        "issue_date": issue_date,
        "rest_start_date": rest_start_date,
        "rest_end_date": rest_end_date,
        "rest_days": rest_days,
        "physician_name": physician_name,
        "physician_department": physician_department,
        "seal_present": bool(seal_text),
        "seal_text": seal_text,
    }
