from __future__ import annotations

import re
from typing import Any

SICK_NOTE_TITLE_RE = re.compile(r"(病休证明书|病休证明|病假单|病假证明|休息证明|医务病休证明书)")
REST_ADVICE_RE = re.compile(r"(建议.{0,8}(休息|病休)|全休|休息\s*\d+\s*(天|日)|病休\s*\d+\s*(天|日))")
DATE_RANGE_RE = re.compile(
    r"((自|从)?\s*\d{4}[年\-/.]\d{1,2}[月\-/.]\d{1,2}日?\s*(至|到)\s*\d{4}[年\-/.]\d{1,2}[月\-/.]\d{1,2}日?|共\s*\d+\s*(天|日))"
)
DIAGNOSIS_RE = re.compile(r"(诊断|初步诊断|临床诊断)")
PHYSICIAN_RE = re.compile(r"(医师|医生|医师签名|签名|签章)")
STAMP_RE = re.compile(r"(盖章|公章|证明专用章|诊断证明章|病假专用章|章)")
HOSPITAL_RE = re.compile(r"(医院|卫生院|医疗中心|门诊部)")
DATE_RE = re.compile(r"\d{4}[年\-/.]\d{1,2}[月\-/.]\d{1,2}日?")

FEATURE_WEIGHTS = {
    "hospital_header": 1.0,
    "sick_leave_title": 1.5,
    "rest_advice": 1.5,
    "date_range": 1.2,
    "diagnosis": 1.0,
    "physician_signature": 0.8,
    "seal_or_stamp": 0.8,
}

FEATURE_LABELS = {
    "hospital_header": "医院抬头",
    "sick_leave_title": "病休/病假标题",
    "rest_advice": "病休/休息建议",
    "date_range": "日期区间/天数",
    "diagnosis": "诊断信息",
    "physician_signature": "医生/医师签名",
    "seal_or_stamp": "盖章/印章",
}


def _rows(ocr_result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for item in ocr_result.get("lines", []):
        text = (item.get("text") or "").strip()
        if text:
            rows.append(text)
    if not rows and ocr_result.get("text"):
        rows = [line.strip() for line in str(ocr_result["text"]).splitlines() if line.strip()]
    return rows


def _normalize_text(rows: list[str]) -> str:
    return "\n".join(rows)


def assess_sick_note_characteristics(
    ocr_result: dict[str, Any],
    *,
    parsed_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parsed_fields = parsed_fields or {}
    rows = _rows(ocr_result)
    joined = _normalize_text(rows)

    feature_hits = {
        "hospital_header": bool(parsed_fields.get("hospital_name") or any(HOSPITAL_RE.search(row) for row in rows[:4])),
        "sick_leave_title": bool(SICK_NOTE_TITLE_RE.search(joined)),
        "rest_advice": bool(REST_ADVICE_RE.search(joined)),
        "date_range": bool(DATE_RANGE_RE.search(joined)),
        "diagnosis": bool(parsed_fields.get("diagnosis")) or bool(DIAGNOSIS_RE.search(joined)),
        "physician_signature": bool(PHYSICIAN_RE.search(joined)),
        "seal_or_stamp": bool(STAMP_RE.search(joined)),
    }

    matched_features = [FEATURE_LABELS[key] for key, hit in feature_hits.items() if hit]
    missing_features = [FEATURE_LABELS[key] for key, hit in feature_hits.items() if not hit]

    total_weight = sum(FEATURE_WEIGHTS.values())
    matched_weight = sum(FEATURE_WEIGHTS[key] for key, hit in feature_hits.items() if hit)
    score = round(matched_weight / total_weight, 3) if total_weight else 0.0

    core_hits = sum(
        1
        for key in ("sick_leave_title", "rest_advice", "date_range", "diagnosis")
        if feature_hits[key]
    )
    is_sick_note_like = (
        feature_hits["sick_leave_title"]
        and feature_hits["rest_advice"]
        and core_hits >= 3
        and score >= 0.6
    )

    if score >= 0.8:
        confidence = "high"
    elif score >= 0.55:
        confidence = "medium"
    else:
        confidence = "low"

    date_matches = DATE_RE.findall(joined)
    title_match = SICK_NOTE_TITLE_RE.search(joined)

    return {
        "is_sick_note_like": is_sick_note_like,
        "score": score,
        "confidence": confidence,
        "matched_features": matched_features,
        "missing_features": missing_features,
        "feature_hits": feature_hits,
        "evidence": {
            "title": title_match.group(0) if title_match else None,
            "date_mentions": date_matches[:4],
            "line_count": len(rows),
        },
    }
