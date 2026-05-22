from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask

logger = logging.getLogger(__name__)


def _is_dry_run() -> bool:
    return str(os.getenv("ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN", "false")).strip().lower() in {"1", "true", "yes", "on"}


def _log_adapter_event(**fields: Any) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    logger.info("leave_audit_adapter_event %s", details)


class LeaveSystemHttpError(RuntimeError):
    """Raised when the upstream leave system returns a non-success HTTP response."""


@dataclass(frozen=True, slots=True)
class HttpLeaveSystemSettings:
    base_url: str
    token: str | None = None
    pending_api: str = "/leave-audit/pending"
    download_api: str = "/leave-audit/download"
    callback_api: str = "/leave-audit/callback"
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "HttpLeaveSystemSettings":
        timeout_raw = os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_TIMEOUT_SECONDS", "10")
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("ID_DOC_OCR_LEAVE_SYSTEM_TIMEOUT_SECONDS must be a number") from exc
        return cls(
            base_url=os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL", "").strip(),
            token=os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_TOKEN") or None,
            pending_api=os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_PENDING_API", "/leave-audit/pending"),
            download_api=os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_DOWNLOAD_API", "/leave-audit/download"),
            callback_api=os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_API", "/leave-audit/callback"),
            timeout_seconds=timeout_seconds,
        )


class HttpLeaveSystemAdapter(LeaveSystemAdapter):
    def __init__(self, settings: HttpLeaveSystemSettings | None = None, client: httpx.Client | None = None) -> None:
        self.settings = settings or HttpLeaveSystemSettings.from_env()
        if not self.settings.base_url:
            raise ValueError("ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL is required when using http leave system adapter")
        self.client = client or httpx.Client(timeout=self.settings.timeout_seconds, trust_env=False)

    def fetch_pending_attachments(self) -> list[LeaveAuditTask]:
        started = time.perf_counter()
        response: httpx.Response | None = None
        error_type = None
        error_message = None
        try:
            response = self.client.get(
                self._url(self.settings.pending_api),
                headers=self._headers(),
            )
            payload = self._json_or_raise(response, "fetch pending leave attachments")
            items = payload.get("tasks", payload.get("data", payload if isinstance(payload, list) else [])) if isinstance(payload, dict) else payload
            if not isinstance(items, list):
                raise ValueError("leave system pending response must be a list or contain a tasks/data list")
            return [self._task_from_payload(item) for item in items]
        except Exception as exc:
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            _log_adapter_event(
                adapter_type=self.__class__.__name__,
                adapter_action="fetch_pending_attachments",
                http_status=response.status_code if response is not None else None,
                elapsed_ms=f"{elapsed_ms:.2f}",
                dry_run=_is_dry_run(),
                error_type=error_type,
                error_message=error_message,
            )

    def download_attachment(self, attachment_url: str) -> bytes:
        started = time.perf_counter()
        response: httpx.Response | None = None
        error_type = None
        error_message = None
        try:
            if attachment_url.startswith("http://") or attachment_url.startswith("https://"):
                url = attachment_url
                params: dict[str, str] | None = None
            else:
                url = self._url(self.settings.download_api)
                params = {"attachment_url": attachment_url}
            response = self.client.get(url, params=params, headers=self._headers())
            self._raise_for_status(response, "download leave attachment")
            return response.content
        except Exception as exc:
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            _log_adapter_event(
                attachment_id=attachment_url,
                adapter_type=self.__class__.__name__,
                adapter_action="download_attachment",
                http_status=response.status_code if response is not None else None,
                elapsed_ms=f"{elapsed_ms:.2f}",
                dry_run=_is_dry_run(),
                error_type=error_type,
                error_message=error_message,
            )

    def push_audit_result(self, result: LeaveAuditResult) -> None:
        started = time.perf_counter()
        response: httpx.Response | None = None
        error_type = None
        error_message = None
        payload = self._callback_payload(result)
        try:
            response = self.client.post(
                self._url(self.settings.callback_api),
                headers=self._headers(),
                json=payload,
            )
            self._raise_for_status(response, "push leave audit result")
        except Exception as exc:
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            _log_adapter_event(
                request_id=result.request_id,
                leave_request_id=payload.get("leave_request_id"),
                adapter_type=self.__class__.__name__,
                adapter_action="push_audit_result",
                http_status=response.status_code if response is not None else None,
                elapsed_ms=f"{elapsed_ms:.2f}",
                dry_run=_is_dry_run(),
                error_type=error_type,
                error_message=error_message,
            )

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        return urljoin(self.settings.base_url.rstrip("/") + "/", path_or_url.lstrip("/"))

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.settings.token:
            headers["Authorization"] = f"Bearer {self.settings.token}"
        return headers

    def _json_or_raise(self, response: httpx.Response, action: str) -> Any:
        self._raise_for_status(response, action)
        try:
            return response.json()
        except ValueError as exc:
            raise ValueError(f"leave system {action} response is not valid JSON") from exc

    def _raise_for_status(self, response: httpx.Response, action: str) -> None:
        if 200 <= response.status_code < 300:
            return
        preview = response.text[:500]
        raise LeaveSystemHttpError(
            f"leave system {action} failed: status={response.status_code} body={preview}"
        )

    def _task_from_payload(self, item: dict[str, Any]) -> LeaveAuditTask:
        attachments_payload = item.get("attachments") or item.get("attachment_list") or []
        if not isinstance(attachments_payload, list):
            raise ValueError("leave system task attachments must be a list")
        attachments = [self._attachment_from_payload(att) for att in attachments_payload]
        status_raw = item.get("status") or "PENDING"
        return LeaveAuditTask(
            request_id=str(item.get("request_id") or item.get("id") or item.get("leave_request_id")),
            leave_type=str(item.get("leave_type") or ""),
            employee_name=str(item.get("employee_name") or item.get("applicant_name") or item.get("applicant") or ""),
            employee_id=item.get("employee_id"),
            leave_start_date=item.get("leave_start_date") or item.get("start_date"),
            leave_end_date=item.get("leave_end_date") or item.get("end_date"),
            status=LeaveAuditStatus(status_raw),
            attachments=attachments,
            raw_payload=dict(item),
        )

    def _attachment_from_payload(self, item: dict[str, Any]) -> LeaveAttachment:
        return LeaveAttachment(
            attachment_id=str(item.get("attachment_id") or item.get("id") or item.get("file_id")),
            attachment_url=str(item.get("attachment_url") or item.get("url") or item.get("download_url")),
            filename=item.get("filename") or item.get("attachment_name") or item.get("name"),
            content_type=item.get("content_type") or item.get("mime_type"),
            plugin_name=item.get("plugin_name"),
            metadata=dict(item.get("metadata") or {}),
        )

    def _callback_payload(self, result: LeaveAuditResult) -> dict[str, Any]:
        verification = result.verification_json or {}
        request_evidence = ((verification.get("evidence") or {}).get("request") or {}) if isinstance(verification.get("evidence"), dict) else {}
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
