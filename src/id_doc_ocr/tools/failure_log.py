from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FAILURE_CASE_SCHEMA_VERSION = "1.0"


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"type": "bytes", "size": len(value)}
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_validation_summary(validation: dict[str, Any] | None) -> dict[str, Any]:
    report = validation or {}
    issues = report.get("issues") or []
    severity_counts = {"error": 0, "warning": 0, "info": 0}
    issue_codes: list[str] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        severity = str(issue.get("severity") or "info")
        if severity in severity_counts:
            severity_counts[severity] += 1
        code = issue.get("code")
        if code:
            issue_codes.append(str(code))
    return {
        "accepted": bool(report.get("accepted", False)),
        "score": report.get("score"),
        "issue_count": len(issues),
        "issue_codes": issue_codes,
        "severity_counts": severity_counts,
    }



def _build_failure_record(payload: dict[str, Any], name: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = metadata or {}
    sample_id = str(meta.get("sample_id") or payload.get("sample_id") or name)
    plugin = meta.get("plugin") or payload.get("plugin")
    backend = {
        "ocr": meta.get("ocr_backend") or payload.get("ocr_backend"),
        "vlm": meta.get("vlm_backend") or payload.get("vlm_backend"),
        "detector": meta.get("detector_backend") or payload.get("detector_backend"),
        "rectify": meta.get("rectify_backend") or payload.get("rectify_backend"),
    }
    source = {
        "kind": meta.get("source_kind") or ("path" if payload.get("sample_id") != "in_memory_sample" else "in_memory"),
        "name": meta.get("source_name"),
    }
    return {
        "schema_version": FAILURE_CASE_SCHEMA_VERSION,
        "recorded_at": _utc_now_iso(),
        "sample_id": sample_id,
        "plugin": plugin,
        "schema": payload.get("schema"),
        "backend": backend,
        "validation": _build_validation_summary(payload.get("validation")),
        "source": source,
        "result": payload,
    }



def write_failure_case(
    out_dir: str | Path,
    payload: dict[str, Any],
    name: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.json"
    record = _build_failure_record(payload, name, metadata=metadata)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=_json_safe))
    return path
