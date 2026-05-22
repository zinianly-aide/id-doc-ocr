from __future__ import annotations

from abc import ABC, abstractmethod

from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult, LeaveAuditTask


class LeaveSystemAdapter(ABC):
    @abstractmethod
    def fetch_pending_attachments(self) -> list[LeaveAuditTask]:
        raise NotImplementedError

    @abstractmethod
    def download_attachment(self, attachment_url: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def push_audit_result(self, result: LeaveAuditResult) -> None:
        raise NotImplementedError
