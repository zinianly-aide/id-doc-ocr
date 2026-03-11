from __future__ import annotations

import re
from typing import Any

DATE_RE = re.compile(r"\b\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?\b")
AGE_RE = re.compile(r"(\d{1,3})\s*岁")
GENDER_TOKENS = {"男": "男", "女": "女", "MALE": "男", "FEMALE": "女"}
LABEL_ALIASES = {
    "hospital_name": ["医院", "医院名称", "HOSPITAL"],
    "patient_name": ["姓名", "患者姓名", "NAME"],
    "gender": ["性别", "SEX", "GENDER"],
    "age": ["年龄", "AGE"],
    "visit_date": ["就诊日期", "日期", "就诊时间", "VISIT DATE", "DATE"],
    "department": ["科别", "科室", "门诊", "DEPARTMENT"],
    "diagnosis": ["诊断", "初步诊断", "DIAGNOSIS"],
    "medications": ["用药", "药品", "处方", "MEDICATION", "RX"],
    "notes": ["主诉", "病史", "备注", "NOTES", "NOTE"],
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
    return f"{yyyy}-{int(mm):02d}-{int(dd):02d}"


def _normalize_gender(value: str | None) -> str | None:
    if not value:
        return None
    upper = value.upper()
    for token, normalized in GENDER_TOKENS.items():
        if token in upper or token in value:
            return normalized
    return value.strip()


def _normalize_age(value: str | None) -> str | None:
    if not value:
        return None
    m = AGE_RE.search(value)
    if m:
        return m.group(1)
    digits = re.findall(r"\d+", value)
    return digits[0] if digits else value.strip()


def _split_items(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[；;、,，]\s*", value)
    return [part.strip() for part in parts if part.strip()]



def parse_medical_record_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(ocr_result)
    joined = "\n".join(rows)

    hospital_name = _collect_labeled_value(rows, "hospital_name")
    if not hospital_name:
        for row in rows[:3]:
            if "医院" in row:
                hospital_name = row.strip()
                break

    patient_name = _collect_labeled_value(rows, "patient_name")
    gender = _normalize_gender(_collect_labeled_value(rows, "gender"))
    age = _normalize_age(_collect_labeled_value(rows, "age"))
    visit_date = _normalize_date(_collect_labeled_value(rows, "visit_date") or joined)
    department = _collect_labeled_value(rows, "department")
    diagnosis = _split_items(_collect_labeled_value(rows, "diagnosis"))
    medications = _split_items(_collect_labeled_value(rows, "medications"))
    notes = _collect_labeled_value(rows, "notes")

    return {
        "doc_type": "medical_record",
        "hospital_name": hospital_name,
        "patient_name": patient_name,
        "gender": gender,
        "age": age,
        "visit_date": visit_date,
        "department": department,
        "diagnosis": diagnosis,
        "medications": medications,
        "notes": notes,
    }
