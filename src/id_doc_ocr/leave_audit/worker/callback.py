from __future__ import annotations

import os
import time
from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult
from id_doc_ocr.leave_audit.repository.base import LeaveAuditRepository


class CallbackOutboxWorker:
    def __init__(self, repository: LeaveAuditRepository, adapter: LeaveSystemAdapter, max_attempts: int = 3) -> None:
        self.repository = repository
        self.adapter = adapter
        self.max_attempts = max_attempts

    def process_pending(self, limit: int = 100) -> int:
        processed = 0
        for item in self.repository.list_pending_callbacks(limit):
            self.repository.mark_callback_processing(item.callback_id)
            payload = item.payload
            status = LeaveAuditStatus(str(payload.get("verify_status") or "REVIEW"))
            result = LeaveAuditResult(request_id=item.request_id, status=status, verification_json=payload,
                                      decision_version=item.decision_version)
            try:
                self.adapter.push_audit_result(result)
            except Exception as exc:
                self.repository.mark_callback_failed(item.callback_id, item.request_id, f"{exc.__class__.__name__}: {exc}", dead=item.attempt_count + 1 >= self.max_attempts)
                continue
            self.repository.mark_callback_succeeded(item.callback_id, item.request_id)
            processed += 1
        return processed

    def run_forever(self, poll_interval: float | None = None) -> None:  # pragma: no cover - process entrypoint
        interval = poll_interval if poll_interval is not None else float(os.getenv("CALLBACK_WORKER_POLL_SECONDS", "5"))
        while True:
            self.process_pending()
            time.sleep(interval)
