from __future__ import annotations

from typing import Any

_RULES = {
    "MEDICAL_CERTIFICATE": ["诊断证明", "诊断证明书", "病休证明", "病假", "休息", "门诊诊断证明书", "医务病休证明书"],
    "MARRIAGE_CERTIFICATE": ["结婚证", "婚姻登记", "持证人", "登记日期", "结婚登记"],
    "BIRTH_CERTIFICATE": ["出生医学证明", "新生儿姓名", "母亲姓名", "父亲姓名"],
    "TRAIN_TICKET": ["中国铁路客票", "火车票", "车次", "检票口", "二等座"],
}


def _flatten_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("lines"), list):
            return "\n".join(str(line.get("text", "")) for line in payload["lines"] if isinstance(line, dict))
        if "text" in payload:
            return str(payload.get("text") or "")
        return "\n".join(_flatten_text(value) for value in payload.values())
    if isinstance(payload, (list, tuple, set)):
        return "\n".join(_flatten_text(item) for item in payload)
    return str(payload)



def classify_leave_attachment(payload: Any) -> dict[str, Any]:
    text = _flatten_text(payload)
    matched_by_label: dict[str, list[str]] = {}

    for label, keywords in _RULES.items():
        matched = [keyword for keyword in keywords if keyword and keyword in text]
        if matched:
            matched_by_label[label] = matched

    if not matched_by_label:
        return {"label": "UNKNOWN", "confidence": 0.0, "matched_keywords": []}

    best_label, matched_keywords = max(matched_by_label.items(), key=lambda item: (len(item[1]), max(len(k) for k in item[1])))
    confidence = round(min(1.0, 0.4 + 0.2 * len(matched_keywords)), 2)
    return {"label": best_label, "confidence": confidence, "matched_keywords": matched_keywords}
