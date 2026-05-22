from __future__ import annotations

from typing import Any

from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.mapping import resolve_plugin_for_leave_task
from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult, LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.verification.rules import verify_attachment


class AuditService:
    def __init__(self, repository: SQLiteRepository, adapter: LeaveSystemAdapter, inference_service: InferenceService | None = None) -> None:
        self.repository = repository
        self.adapter = adapter
        self.inference_service = inference_service or InferenceService()

    def run_task(self, request_id: str) -> LeaveAuditResult:
        task = self.repository.get_task(request_id)
        if task is None:
            raise KeyError(f"Leave audit task not found: {request_id}")
        return self.process_task(task)

    def process_task(self, task: LeaveAuditTask) -> LeaveAuditResult:
        self.repository.update_task_status(task.request_id, LeaveAuditStatus.PROCESSING)
        try:
            if not task.attachments:
                raise ValueError("task has no attachments")
            attachment = task.attachments[0]
            plugin_name = resolve_plugin_for_leave_task(task)
            payload = self.adapter.download_attachment(attachment.attachment_url)
            mock_fields = dict(attachment.metadata.get("mock_fields") or task.raw_payload.get("mock_fields") or {})
            analysis_result = self.inference_service.run(
                plugin_name=plugin_name,
                image=payload,
                filename=attachment.filename or f"{attachment.attachment_id}.jpg",
                fields=mock_fields,
            )
            analysis_json = analysis_result["analysis"]
            verification_request: dict[str, Any] = {
                "leave_type": task.leave_type,
                "applicant_name": task.employee_name,
                "leave_start_date": task.leave_start_date,
                "leave_end_date": task.leave_end_date,
            }
            verification_request.update(dict(task.raw_payload.get("verification_context") or {}))
            verification_json = verify_attachment(analysis_json, verification_request)
            status = LeaveAuditStatus(str(verification_json.get("verify_status") or "REVIEW"))
            result = LeaveAuditResult(
                request_id=task.request_id,
                status=status,
                plugin_name=plugin_name,
                analysis_json=analysis_json,
                verification_json=verification_json,
            )
        except Exception as exc:
            result = LeaveAuditResult(
                request_id=task.request_id,
                status=LeaveAuditStatus.ERROR,
                analysis_json={},
                verification_json={},
                error_message=f"{exc.__class__.__name__}: {exc}",
            )
        self.repository.save_result(result)
        self.repository.update_task_status(task.request_id, result.status)
        return result

    def push_callback(self, request_id: str) -> LeaveAuditResult:
        result = self.repository.get_result(request_id)
        if result is None:
            raise KeyError(f"Leave audit result not found: {request_id}")
        self.adapter.push_audit_result(result)
        result.synced = True
        self.repository.save_result(result)
        self.repository.update_task_status(request_id, LeaveAuditStatus.SYNCED)
        return result
