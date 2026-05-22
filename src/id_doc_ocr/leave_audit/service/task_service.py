from __future__ import annotations

import logging
import time
from typing import Any

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.audit_service import is_leave_audit_dry_run

logger = logging.getLogger(__name__)


def _log_task_event(**fields: Any) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    logger.info("leave_audit_event %s", details)


class TaskService:
    def __init__(self, repository: SQLiteRepository, adapter: LeaveSystemAdapter) -> None:
        self.repository = repository
        self.adapter = adapter

    def sync_pending(self) -> list[LeaveAuditTask]:
        started = time.perf_counter()
        error_type = None
        error_message = None
        try:
            tasks = self.adapter.fetch_pending_attachments()
            for task in tasks:
                task.status = LeaveAuditStatus.PULLED
                self.repository.save_task(task)
            return tasks
        except Exception as exc:
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            _log_task_event(
                adapter_type=self.adapter.__class__.__name__,
                adapter_action="sync_pending",
                http_status=None,
                elapsed_ms=f"{elapsed_ms:.2f}",
                dry_run=is_leave_audit_dry_run(),
                error_type=error_type,
                error_message=error_message,
            )
