from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class LeaveAttachment:
    attachment_id: str
    attachment_url: str
    filename: str | None = None
    content_type: str | None = None
    plugin_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LeaveAuditTask:
    request_id: str
    leave_type: str
    employee_name: str
    leave_start_date: str | None = None
    leave_end_date: str | None = None
    status: LeaveAuditStatus = LeaveAuditStatus.PENDING
    attachments: list[LeaveAttachment] = field(default_factory=list)
    employee_id: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class LeaveAuditResult:
    request_id: str
    status: LeaveAuditStatus
    plugin_name: str | None = None
    analysis_json: dict[str, Any] = field(default_factory=dict)
    verification_json: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    synced: bool = False
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class LeaveReviewDecision:
    request_id: str
    decision: LeaveAuditStatus
    reviewer: str
    comment: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
