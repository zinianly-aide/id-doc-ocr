from __future__ import annotations

from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult
from id_doc_ocr.leave_audit.service.audit_service import AuditService


class LeaveAuditProcessor:
    def __init__(self, audit_service: AuditService) -> None:
        self.audit_service = audit_service

    def process(self, request_id: str) -> LeaveAuditResult:
        return self.audit_service.run_task(request_id)
