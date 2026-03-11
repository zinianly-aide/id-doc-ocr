from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"\b\d{2}[A-Z]{3}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{2}:\d{2}\b")
TRAIN_RE = re.compile(r"\b([GDCZTKYLSP]?\d{1,4})\b")
FLIGHT_RE = re.compile(r"\b([A-Z]{1,2}\s?\d{3,4})\b")
TKT_RE = re.compile(r"(?:ETKT\s?)(\d{10,14}(?:/\d)?)", re.IGNORECASE)
GATE_RE = re.compile(r"\bG\d{1,2}\b")
NAME_RE = re.compile(r"^[A-Z][A-Z\s]{4,24}$")
AIRPORTS = {"TAIYUAN", "FUZHOU", "SHANGHAI", "HANGZHOU", "BEIJING", "GUANGZHOU"}
TRAIN_STATIONS = {"SHANGHAI", "HANGZHOU", "BEIJING", "GUANGZHOU", "NANJING", "SUZHOU", "WUHAN"}
STOPWORDS = {"BOARDING PASS", "BOARDING", "PASS", "FLIGHT", "DATE", "CLASS", "NAME", "FROM", "TO"}


def _rows(ocr_result: dict[str, Any]) -> list[dict[str, Any]]:
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
        rows.append({"text": text, "score": float(item.get("score", 0.0) or 0.0), "bbox": bbox})
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
        upper = row['text'].upper().replace(' ', '')
        if any(k.replace(' ', '') in upper for k in keywords):
            return row
    return None


def parse_train_ticket_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(ocr_result)
    joined = '\n'.join(r['text'] for r in rows)
    fields: dict[str, Any] = {
        'document_variant': 'train_ticket',
        'ticket_number': None,
        'passenger_name': None,
        'train_number': None,
        'departure_station': None,
        'arrival_station': None,
        'departure_time': None,
        'seat_no': None,
        'fare': None,
        'gate': None,
    }

    if 'BOARDING' in joined.upper() or 'FLIGHT' in joined.upper() or '登机牌' in joined:
        fields['document_variant'] = 'boarding_pass_like'

    m = TKT_RE.search(joined)
    if m:
        fields['ticket_number'] = m.group(1)

    m = GATE_RE.search(joined)
    if m:
        fields['gate'] = m.group(0)

    dates = DATE_RE.findall(joined)
    if dates:
        fields['departure_time'] = dates[0]

    # prefer train-number-like patterns unless boarding-pass-like content dominates
    if fields['document_variant'] == 'boarding_pass_like':
        m = FLIGHT_RE.search(joined)
        if m:
            fields['train_number'] = m.group(1).replace(' ', '')
    else:
        candidates = []
        for row in rows:
            m = TRAIN_RE.search(row['text'].upper())
            if not m:
                continue
            value = m.group(1)
            if value.isdigit():
                continue
            candidates.append((row['score'], value))
        if candidates:
            candidates.sort(reverse=True)
            fields['train_number'] = candidates[0][1]

    # station / airport extraction
    station_candidates = []
    for row in rows:
        upper = row['text'].upper().replace(' ', '')
        if fields['document_variant'] == 'boarding_pass_like':
            if upper in AIRPORTS and upper not in station_candidates:
                station_candidates.append(upper)
        else:
            if upper in TRAIN_STATIONS and upper not in station_candidates:
                station_candidates.append(upper)
    if len(station_candidates) >= 1:
        fields['departure_station'] = station_candidates[0]
    if len(station_candidates) >= 2:
        fields['arrival_station'] = station_candidates[1]

    # name extraction using NAME anchor when present
    name_anchor = _find_anchor(rows, ['姓名', 'NAME'])
    candidates = []
    for row in rows:
        text = re.sub(r'\s+', ' ', row['text'].upper()).strip()
        if text in STOPWORDS or text in AIRPORTS or text in TRAIN_STATIONS:
            continue
        if any(token in text for token in ['ETKT', 'TKTNO', 'FLIGHT', 'GATE', 'DATE', 'SEAT', 'FROM', 'TO']):
            continue
        if len(text) > 24:
            continue
        if not NAME_RE.match(text):
            continue
        candidates.append((_distance(row.get('bbox'), name_anchor.get('bbox') if name_anchor else None), -row['score'], text))
    if candidates:
        candidates.sort()
        fields['passenger_name'] = candidates[0][2]

    return fields
