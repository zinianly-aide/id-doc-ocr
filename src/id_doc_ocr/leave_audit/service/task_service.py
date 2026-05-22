from __future__ import annotations

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


class TaskService:
    def __init__(self, repository: SQLiteRepository, adapter: LeaveSystemAdapter) -> None:
        self.repository = repository
        self.adapter = adapter

    def sync_pending(self) -> list[LeaveAuditTask]:
        tasks = self.adapter.fetch_pending_attachments()
        for task in tasks:
            task.status = LeaveAuditStatus.PULLED
            self.repository.save_task(task)
        return tasks
