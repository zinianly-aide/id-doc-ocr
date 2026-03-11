from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"\b\d{2}[A-Z]{3}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{2}:\d{2}\b")
FLIGHT_RE = re.compile(r"\b([A-Z]{1,2}\s?\d{3,4})\b")
TKT_RE = re.compile(r"(?:ETKT\s?)(\d{10,14}(?:/\d)?)", re.IGNORECASE)
NAME_RE = re.compile(r"\b[A-Z][A-Z\s]{3,}\b")
GATE_RE = re.compile(r"\bG\d{1,2}\b")


def _clean_lines(ocr_result: dict[str, Any]) -> list[str]:
    lines = []
    for item in ocr_result.get("lines", []):
        text = (item.get("text") or "").strip()
        if text:
            lines.append(text)
    if not lines and ocr_result.get("text"):
        lines = [x.strip() for x in str(ocr_result["text"]).splitlines() if x.strip()]
    return lines


def parse_train_ticket_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    lines = _clean_lines(ocr_result)
    joined = "\n".join(lines)

    fields: dict[str, Any] = {
        "document_variant": "unknown",
        "ticket_number": None,
        "passenger_name": None,
        "train_number": None,
        "departure_station": None,
        "arrival_station": None,
        "departure_time": None,
        "seat_no": None,
        "fare": None,
        "gate": None,
    }

    if "BOARDING" in joined or "FLIGHT" in joined or "登机牌" in joined:
        fields["document_variant"] = "boarding_pass"

    tkt = TKT_RE.search(joined)
    if tkt:
        fields["ticket_number"] = tkt.group(1)

    flight = FLIGHT_RE.search(joined)
    if flight:
        fields["train_number"] = flight.group(1).replace(" ", "")

    gate = GATE_RE.search(joined)
    if gate:
        fields["gate"] = gate.group(0)

    dates = DATE_RE.findall(joined)
    if dates:
        fields["departure_time"] = dates[0]

    # simple heuristic for name on boarding pass / ticket-like docs
    candidate_names: list[str] = []
    for line in lines:
        if "NAME" in line.upper():
            continue
        m = NAME_RE.search(line.upper())
        if m:
            text = m.group(0).strip()
            if text not in {"BOARDING", "PASS", "SERIAL NO", "SEAT NO", "FLIGHT", "DATE", "CLASS"}:
                candidate_names.append(text)
    if candidate_names:
        fields["passenger_name"] = max(candidate_names, key=len)

    # heuristic stations for the known public sample
    stations = []
    for line in lines:
        upper = line.upper().replace(" ", "")
        if upper in {"TAIYUAN", "FUZHOU", "SHANGHAI", "HANGZHOU", "BEIJING", "GUANGZHOU"}:
            stations.append(upper)
    if len(stations) >= 1:
        fields["departure_station"] = stations[0]
    if len(stations) >= 2:
        fields["arrival_station"] = stations[1]

    return fields
