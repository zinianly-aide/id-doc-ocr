from __future__ import annotations

from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult
from id_doc_ocr.leave_audit.service.audit_service import AuditService
from id_doc_ocr.leave_audit.service.task_service import TaskService


class LeaveAuditPoller:
    def __init__(self, task_service: TaskService, audit_service: AuditService) -> None:
        self.task_service = task_service
        self.audit_service = audit_service

    def poll_once(self) -> list[LeaveAuditResult]:
        tasks = self.task_service.sync_pending()
        return [self.audit_service.process_task(task) for task in tasks]
