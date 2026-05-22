from __future__ import annotations

import json
from pathlib import Path

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask

DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[4] / "fixtures" / "sample_leave_tasks.json"


class MockLeaveSystemAdapter(LeaveSystemAdapter):
    def __init__(self, fixture_path: str | Path | None = None) -> None:
        self.fixture_path = Path(fixture_path) if fixture_path else DEFAULT_FIXTURE_PATH
        self.pushed_results: list[LeaveAuditResult] = []

    def fetch_pending_attachments(self) -> list[LeaveAuditTask]:
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        tasks: list[LeaveAuditTask] = []
        for item in payload.get("tasks", payload if isinstance(payload, list) else []):
            attachments = [
                LeaveAttachment(
                    attachment_id=str(att.get("attachment_id") or att.get("id")),
                    attachment_url=str(att.get("attachment_url") or att.get("url")),
                    filename=att.get("filename"),
                    content_type=att.get("content_type"),
                    plugin_name=att.get("plugin_name"),
                    metadata=dict(att.get("metadata") or {}),
                )
                for att in item.get("attachments", [])
            ]
            tasks.append(
                LeaveAuditTask(
                    request_id=str(item["request_id"]),
                    leave_type=str(item["leave_type"]),
                    employee_name=str(item.get("employee_name") or item.get("applicant_name") or ""),
                    employee_id=item.get("employee_id"),
                    leave_start_date=item.get("leave_start_date"),
                    leave_end_date=item.get("leave_end_date"),
                    status=LeaveAuditStatus(item.get("status", "PENDING")),
                    attachments=attachments,
                    raw_payload=dict(item),
                )
            )
        return tasks

    def download_attachment(self, attachment_url: str) -> bytes:
        if attachment_url.startswith("fixture://"):
            return f"mock-image-bytes:{attachment_url}".encode("utf-8")
        path = Path(attachment_url)
        if not path.is_absolute():
            path = self.fixture_path.parent / path
        return path.read_bytes()

    def push_audit_result(self, result: LeaveAuditResult) -> None:
        self.pushed_results.append(result)
