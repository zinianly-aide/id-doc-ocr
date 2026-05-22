from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_FIELD_MAPPING: dict[str, list[str]] = {
    "request_id": ["request_id", "requestId", "id"],
    "leave_request_id": ["leave_request_id", "leaveRequestId", "applyNo", "requestNo"],
    "employee_id": ["employee_id", "employeeId", "empNo"],
    "employee_name": ["employee_name", "employeeName", "empName", "applicant_name", "applicant"],
    "leave_type": ["leave_type", "leaveType", "absenceType"],
    "leave_start_date": ["leave_start_date", "leaveStartDate", "startDate", "startTime"],
    "leave_end_date": ["leave_end_date", "leaveEndDate", "endDate", "endTime"],
    "attachment_id": ["attachment_id", "attachmentId", "fileId", "file_id", "id"],
    "attachment_name": ["attachment_name", "attachmentName", "fileName", "filename", "name"],
    "attachment_url": ["attachment_url", "attachmentUrl", "fileUrl", "url", "download_url"],
    "plugin_name": ["plugin_name", "pluginName"],
    "content_type": ["content_type", "contentType", "mime_type", "mimeType"],
}

DEFAULT_MAPPING_FILE = Path(__file__).resolve().parents[4] / "configs" / "leave_system_field_mapping.yaml"
MAPPING_FILE_ENV = "ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE"

_TASK_REQUIRED_FIELDS = ("leave_request_id", "employee_name", "leave_type")
_ATTACHMENT_REQUIRED_FIELDS = ("attachment_id", "attachment_url")


def _merge_mapping(base: dict[str, list[str]], override: dict[str, Any]) -> dict[str, list[str]]:
    merged = {key: list(values) for key, values in base.items()}
    for canonical_name, aliases_raw in override.items():
        if isinstance(aliases_raw, str):
            aliases = [aliases_raw]
        elif isinstance(aliases_raw, list):
            aliases = [str(alias) for alias in aliases_raw if str(alias).strip()]
        else:
            continue
        existing = merged.setdefault(str(canonical_name), [])
        for alias in aliases:
            if alias not in existing:
                existing.append(alias)
    return merged


def _parse_simple_yaml_mapping(text: str) -> dict[str, list[str]]:
    """Parse the small `key: [list]` YAML subset used by field mapping files.

    PyYAML is intentionally optional for this project. This fallback supports the
    repo's checked-in mapping shape and sandbox override files like:

    canonical_name:
      - aliasOne
      - alias_two
    """
    parsed: dict[str, list[str]] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")) and line.endswith(":"):
            current_key = line[:-1].strip()
            parsed.setdefault(current_key, [])
            continue
        stripped = line.strip()
        if current_key and stripped.startswith("-"):
            value = stripped[1:].strip().strip('"').strip("'")
            if value:
                parsed[current_key].append(value)
            continue
        raise ValueError("field mapping YAML must be a simple mapping of canonical names to alias lists")
    return parsed


def _load_mapping_file(path: Path) -> dict[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        loaded = json.loads(text)
    else:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError:
            loaded = _parse_simple_yaml_mapping(text)
        else:
            loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"field mapping file must contain an object: {path}")
    return {str(key): list(value if isinstance(value, list) else [value]) for key, value in loaded.items()}


def load_field_mapping(mapping_file: str | os.PathLike[str] | None = None) -> dict[str, list[str]]:
    """Load built-in field aliases and merge a repo/env override file if present."""
    configured_path = mapping_file or os.getenv(MAPPING_FILE_ENV)
    path = Path(configured_path).expanduser() if configured_path else DEFAULT_MAPPING_FILE
    if not path.exists():
        return {key: list(values) for key, values in DEFAULT_FIELD_MAPPING.items()}
    return _merge_mapping(DEFAULT_FIELD_MAPPING, _load_mapping_file(path))


def resolve_field(payload: dict[str, Any], canonical_name: str) -> Any:
    """Resolve a canonical internal field from an external payload dict."""
    aliases = load_field_mapping().get(canonical_name, [canonical_name])
    for alias in aliases:
        if alias in payload and payload[alias] not in (None, ""):
            return payload[alias]
    return None


def _normalize_attachment(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "attachment_id": resolve_field(payload, "attachment_id"),
        "attachment_name": resolve_field(payload, "attachment_name"),
        "attachment_url": resolve_field(payload, "attachment_url"),
        "plugin_name": resolve_field(payload, "plugin_name"),
        "content_type": resolve_field(payload, "content_type"),
    }
    for field_name in _ATTACHMENT_REQUIRED_FIELDS:
        if not normalized.get(field_name):
            aliases = ", ".join(load_field_mapping().get(field_name, [field_name]))
            raise ValueError(f"missing required attachment field '{field_name}' in leave system pending item; accepted aliases: {aliases}")
    metadata = payload.get("metadata")
    normalized["metadata"] = dict(metadata) if isinstance(metadata, dict) else {}
    normalized["raw_payload"] = dict(payload)
    return normalized


def normalize_pending_item(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize one pending leave-system item into canonical sidecar fields."""
    if not isinstance(payload, dict):
        raise ValueError("leave system pending item must be an object")

    normalized: dict[str, Any] = {
        "request_id": resolve_field(payload, "request_id"),
        "leave_request_id": resolve_field(payload, "leave_request_id"),
        "employee_id": resolve_field(payload, "employee_id"),
        "employee_name": resolve_field(payload, "employee_name"),
        "leave_type": resolve_field(payload, "leave_type"),
        "leave_start_date": resolve_field(payload, "leave_start_date"),
        "leave_end_date": resolve_field(payload, "leave_end_date"),
        "status": payload.get("status") or "PENDING",
        "raw_payload": dict(payload),
    }
    normalized["request_id"] = normalized["request_id"] or normalized["leave_request_id"]
    normalized["leave_request_id"] = normalized["leave_request_id"] or normalized["request_id"]

    for field_name in _TASK_REQUIRED_FIELDS:
        if not normalized.get(field_name):
            aliases = ", ".join(load_field_mapping().get(field_name, [field_name]))
            raise ValueError(f"missing required field '{field_name}' in leave system pending item; accepted aliases: {aliases}")

    attachments_payload = payload.get("attachments") or payload.get("attachment_list") or payload.get("attachmentList")
    if attachments_payload is None:
        top_level_attachment = {
            "attachment_id": resolve_field(payload, "attachment_id"),
            "attachment_name": resolve_field(payload, "attachment_name"),
            "attachment_url": resolve_field(payload, "attachment_url"),
            "plugin_name": resolve_field(payload, "plugin_name"),
            "content_type": resolve_field(payload, "content_type"),
        }
        attachments_payload = [payload] if any(top_level_attachment.values()) else []
    if not isinstance(attachments_payload, list):
        raise ValueError("leave system task attachments must be a list")

    normalized["attachments"] = [_normalize_attachment(attachment) for attachment in attachments_payload]
    return normalized
