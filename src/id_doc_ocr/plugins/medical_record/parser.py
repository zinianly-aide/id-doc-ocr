from __future__ import annotations

from typing import Any

from id_doc_ocr.plugins.medical_record.common import (
    collect_labeled_value,
    normalize_age,
    normalize_date,
    normalize_gender,
    rows_from_ocr,
    split_items,
)
from id_doc_ocr.plugins.medical_record.sick_note import assess_sick_note_characteristics

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


def _collect_labeled_value(rows: list[str], field: str) -> str | None:
    return collect_labeled_value(rows, LABEL_ALIASES[field])



def parse_medical_record_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_ocr(ocr_result)
    joined = "\n".join(rows)

    hospital_name = _collect_labeled_value(rows, "hospital_name")
    if not hospital_name:
        for row in rows[:3]:
            if "医院" in row:
                hospital_name = row.strip()
                break

    patient_name = _collect_labeled_value(rows, "patient_name")
    gender = normalize_gender(_collect_labeled_value(rows, "gender"))
    age = normalize_age(_collect_labeled_value(rows, "age"))
    visit_date = normalize_date(_collect_labeled_value(rows, "visit_date") or joined)
    department = _collect_labeled_value(rows, "department")
    diagnosis = split_items(_collect_labeled_value(rows, "diagnosis"))
    medications = split_items(_collect_labeled_value(rows, "medications"))
    notes = _collect_labeled_value(rows, "notes")

    fields = {
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
    fields["sick_note_check"] = assess_sick_note_characteristics(ocr_result, parsed_fields=fields)
    return fields
