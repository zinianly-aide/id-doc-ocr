from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"\b\d{2}[A-Z]{3}\b")
FLIGHT_RE = re.compile(r"\b([A-Z]{1,2}\s?\d{3,4})\b")
TKT_RE = re.compile(r"(?:ETKT\s?)(\d{10,14}(?:/\d)?)", re.IGNORECASE)
GATE_RE = re.compile(r"\bG\d{1,2}\b")
NAME_RE = re.compile(r"^[A-Z][A-Z\s]{4,24}$")
AIRPORTS = {"TAIYUAN", "FUZHOU", "SHANGHAI", "HANGZHOU", "BEIJING", "GUANGZHOU"}
STOPWORDS = {
    "BOARDING PASS",
    "BOARDING",
    "PASS",
    "SERIAL NO",
    "SEAT NO",
    "FLIGHT",
    "DATE",
    "CLASS",
    "NAME",
    "NAME NAME",
}


def _clean_lines_with_boxes(ocr_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in ocr_result.get("lines", []):
        text = (item.get("text") or "").strip()
        if not text:
            continue
        box = item.get("box")
        bbox = None
        if isinstance(box, list) and len(box) == 4:
            try:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            except Exception:
                bbox = None
        rows.append({
            "text": text,
            "score": float(item.get("score", 0.0) or 0.0),
            "bbox": bbox,
        })
    if not rows and ocr_result.get("text"):
        for line in str(ocr_result["text"]).splitlines():
            line = line.strip()
            if line:
                rows.append({"text": line, "score": 0.0, "bbox": None})
    return rows


def _distance(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b:
        return 10**9
    ax = (a[0] + a[2]) / 2
    ay = (a[1] + a[3]) / 2
    bx = (b[0] + b[2]) / 2
    by = (b[1] + b[3]) / 2
    return abs(ax - bx) + abs(ay - by)


def _find_anchor(rows: list[dict[str, Any]], keywords: list[str]) -> dict[str, Any] | None:
    for row in rows:
        upper = row["text"].upper().replace(" ", "")
        if any(k.replace(" ", "") in upper for k in keywords):
            return row
    return None


def _best_name_candidate(rows: list[dict[str, Any]], anchor_bbox: list[float] | None) -> str | None:
    candidates = []
    for row in rows:
        text = re.sub(r"\s+", " ", row["text"].upper()).strip()
        if text in STOPWORDS or text in AIRPORTS:
            continue
        if any(token in text for token in ["FLIGHT", "DATE", "GATE", "ETKT", "TKTNO", "SEAT", "FROM", "TO"]):
            continue
        if len(text) > 24:
            continue
        if not NAME_RE.match(text):
            continue
        score = row["score"]
        dist = _distance(row.get("bbox"), anchor_bbox)
        candidates.append((dist, -score, text))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][2]


def _extract_airports(rows: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    airports = []
    for row in rows:
        upper = row["text"].upper().replace(" ", "")
        if upper in AIRPORTS and upper not in airports:
            airports.append(upper)
    dep = airports[0] if len(airports) >= 1 else None
    arr = airports[1] if len(airports) >= 2 else None
    return dep, arr


def parse_boarding_pass_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _clean_lines_with_boxes(ocr_result)
    joined = "\n".join(r["text"] for r in rows)
    fields: dict[str, Any] = {
        "document_variant": "boarding_pass",
        "passenger_name": None,
        "flight_number": None,
        "ticket_number": None,
        "departure_date": None,
        "departure_airport": None,
        "arrival_airport": None,
        "gate": None,
        "seat_no": None,
    }

    m = FLIGHT_RE.search(joined)
    if m:
        fields["flight_number"] = m.group(1).replace(" ", "")
    m = TKT_RE.search(joined)
    if m:
        fields["ticket_number"] = m.group(1)
    m = GATE_RE.search(joined)
    if m:
        fields["gate"] = m.group(0)
    dates = DATE_RE.findall(joined)
    if dates:
        fields["departure_date"] = dates[0]

    dep, arr = _extract_airports(rows)
    fields["departure_airport"] = dep
    fields["arrival_airport"] = arr

    name_anchor = _find_anchor(rows, ["姓名", "NAME"])
    fields["passenger_name"] = _best_name_candidate(rows, name_anchor.get("bbox") if name_anchor else None)
    return fields
