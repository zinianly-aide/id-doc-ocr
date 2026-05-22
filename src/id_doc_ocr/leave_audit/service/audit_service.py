from __future__ import annotations

import logging
import os
import time
from typing import Any

from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.mapping import resolve_plugin_for_leave_task
from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult, LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.verification.rules import verify_attachment

logger = logging.getLogger(__name__)


def is_leave_audit_dry_run() -> bool:
    return str(os.getenv("ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN", "false")).strip().lower() in {"1", "true", "yes", "on"}


def _adapter_type(adapter: LeaveSystemAdapter) -> str:
    return adapter.__class__.__name__


def _leave_request_id_from_task(task: LeaveAuditTask) -> str:
    return str(task.raw_payload.get("leave_request_id") or task.raw_payload.get("request_id") or task.request_id)


def _callback_payload_from_result(result: LeaveAuditResult) -> dict[str, Any]:
    verification = result.verification_json or {}
    evidence = verification.get("evidence") if isinstance(verification.get("evidence"), dict) else {}
    request_evidence = (evidence or {}).get("request") or {}
    return {
        "request_id": result.request_id,
        "leave_request_id": request_evidence.get("leave_request_id") or request_evidence.get("request_id") or result.request_id,
        "verify_status": verification.get("verify_status") or result.status.value,
        "risk_level": verification.get("risk_level"),
        "risk_score": verification.get("risk_score"),
        "needs_manual_review": verification.get("needs_manual_review", result.status != LeaveAuditStatus.PASS),
        "summary": verification.get("summary_message") or result.error_message,
        "rule_results": verification.get("rule_results") or [],
    }


def _log_audit_event(**fields: Any) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    logger.info("leave_audit_event %s", details)


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
        started = time.perf_counter()
        attachment_id = None
        try:
            if not task.attachments:
                raise ValueError("task has no attachments")
            attachment = task.attachments[0]
            attachment_id = attachment.attachment_id
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
                "request_id": task.request_id,
                "leave_request_id": _leave_request_id_from_task(task),
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
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.repository.save_result(result)
        self.repository.update_task_status(task.request_id, result.status)
        _log_audit_event(
            request_id=task.request_id,
            leave_request_id=_leave_request_id_from_task(task),
            attachment_id=attachment_id,
            adapter_type=_adapter_type(self.adapter),
            adapter_action="process_task",
            http_status=None,
            elapsed_ms=f"{elapsed_ms:.2f}",
            dry_run=is_leave_audit_dry_run(),
            error_type=None if result.status != LeaveAuditStatus.ERROR else "processing_error",
            error_message=result.error_message,
        )
        return result

    def push_callback(self, request_id: str) -> LeaveAuditResult:
        result, _ = self.push_callback_with_metadata(request_id)
        return result

    def push_callback_with_metadata(self, request_id: str) -> tuple[LeaveAuditResult, dict[str, Any]]:
        result = self.repository.get_result(request_id)
        if result is None:
            raise KeyError(f"Leave audit result not found: {request_id}")
        started = time.perf_counter()
        dry_run = is_leave_audit_dry_run()
        callback_payload = _callback_payload_from_result(result)
        metadata = {"dry_run": dry_run, "callback_skipped": dry_run, "callback_payload": callback_payload}
        error_type = None
        error_message = None
        try:
            if dry_run:
                result.verification_json = dict(result.verification_json or {})
                result.verification_json["callback_dry_run"] = {
                    "dry_run": True,
                    "callback_skipped": True,
                    "payload": callback_payload,
                }
            else:
                self.adapter.push_audit_result(result)
                result.synced = True
                self.repository.update_task_status(request_id, LeaveAuditStatus.SYNCED)
            self.repository.save_result(result)
            return result, metadata
        except Exception as exc:
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            _log_audit_event(
                request_id=request_id,
                leave_request_id=callback_payload.get("leave_request_id"),
                attachment_id=None,
                adapter_type=_adapter_type(self.adapter),
                adapter_action="callback",
                http_status=None,
                elapsed_ms=f"{elapsed_ms:.2f}",
                dry_run=dry_run,
                error_type=error_type,
                error_message=error_message,
            )
