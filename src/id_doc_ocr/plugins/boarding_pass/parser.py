from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"\b\d{2}[A-Z]{3}\b")
FLIGHT_RE = re.compile(r"\b([A-Z]{1,2}\s?\d{3,4})\b")
TKT_RE = re.compile(r"(?:ETKT\s?)(\d{10,14}(?:/\d)?)", re.IGNORECASE)
GATE_RE = re.compile(r"\bG\d{1,2}\b")
UPPER_WORD_RE = re.compile(r"\b[A-Z][A-Z\s]{4,}\b")

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
    "GATES CLOSE MINUTES BEFORE DEPARTURE TIME",
    "GATESCLOSEIOMINUTESBEFOREDEPARTURETIME",
}


def _clean_lines(ocr_result: dict[str, Any]) -> list[str]:
    lines = []
    for item in ocr_result.get("lines", []):
        text = (item.get("text") or "").strip()
        if text:
            lines.append(text)
    if not lines and ocr_result.get("text"):
        lines = [x.strip() for x in str(ocr_result["text"]).splitlines() if x.strip()]
    return lines


def parse_boarding_pass_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    lines = _clean_lines(ocr_result)
    joined = "\n".join(lines)
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

    airports = []
    for line in lines:
        upper = line.upper().replace(" ", "")
        if upper in AIRPORTS and upper not in airports:
            airports.append(upper)
    if len(airports) >= 1:
        fields["departure_airport"] = airports[0]
    if len(airports) >= 2:
        fields["arrival_airport"] = airports[1]

    candidates = []
    for line in lines:
        upper = line.upper().strip()
        if any(token in upper for token in ["NAME", "TKTNO", "FLIGHT", "GATE", "DATE", "SEAT"]):
            continue
        found = UPPER_WORD_RE.search(upper)
        if found:
            text = re.sub(r"\s+", " ", found.group(0)).strip()
            if text in STOPWORDS:
                continue
            if text in AIRPORTS:
                continue
            if len(text) > 24:
                continue
            candidates.append(text)
    if candidates:
        fields["passenger_name"] = max(candidates, key=len)

    return fields
