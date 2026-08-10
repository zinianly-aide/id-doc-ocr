from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from id_doc_ocr.leave_audit.domain.async_status import CallbackStatus, DecisionStatus, OcrJobStatus
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
    # ``status`` remains as a compatibility field for existing callers. New
    # code must use the three orthogonal statuses below.
    ocr_status: OcrJobStatus = OcrJobStatus.CREATED
    decision_status: DecisionStatus = DecisionStatus.PENDING
    callback_status: CallbackStatus = CallbackStatus.NOT_REQUIRED
    decision_version: int = 0
    ocr_profile_snapshot_id: str | None = None
    decision_policy_snapshot_id: str | None = None
    field_mapping_snapshot_id: str | None = None
    callback_policy_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        if self.status is LeaveAuditStatus.PROCESSING:
            self.ocr_status = OcrJobStatus.PROCESSING
        elif self.status is LeaveAuditStatus.PASS:
            self.ocr_status = OcrJobStatus.SUCCEEDED
            self.decision_status = DecisionStatus.PASS
        elif self.status is LeaveAuditStatus.REVIEW:
            self.ocr_status = OcrJobStatus.SUCCEEDED
            self.decision_status = DecisionStatus.REVIEW_REQUIRED
        elif self.status is LeaveAuditStatus.REJECT:
            self.ocr_status = OcrJobStatus.SUCCEEDED
            self.decision_status = DecisionStatus.REJECT
        elif self.status is LeaveAuditStatus.ERROR:
            self.ocr_status = OcrJobStatus.FAILED
        elif self.status is LeaveAuditStatus.PULLED and self.ocr_status is OcrJobStatus.CREATED:
            self.ocr_status = OcrJobStatus.CREATED


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
    job_id: str | None = None
    attachment_id: str | None = None
    ocr_status: OcrJobStatus = OcrJobStatus.SUCCEEDED
    decision_status: DecisionStatus | None = None
    callback_status: CallbackStatus = CallbackStatus.NOT_REQUIRED
    decision_version: int = 0
    ocr_profile_snapshot_id: str | None = None
    decision_policy_snapshot_id: str | None = None
    field_mapping_snapshot_id: str | None = None
    callback_policy_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        if self.status is LeaveAuditStatus.ERROR:
            self.ocr_status = OcrJobStatus.FAILED
        if self.decision_status is None:
            self.decision_status = {
                LeaveAuditStatus.PASS: DecisionStatus.PASS,
                LeaveAuditStatus.REVIEW: DecisionStatus.REVIEW_REQUIRED,
                LeaveAuditStatus.REJECT: DecisionStatus.REJECT,
            }.get(self.status)
        if self.synced:
            self.callback_status = CallbackStatus.SUCCEEDED


@dataclass(slots=True)
class LeaveReviewDecision:
    request_id: str
    decision: LeaveAuditStatus
    reviewer: str
    comment: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
