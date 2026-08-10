from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.contracts.ocr import OcrCommandV1, OcrResultEventV1
from id_doc_ocr.leave_audit.storage.base import ObjectStorage, sha256_hex
from id_doc_ocr.utils.document_pages import expand_document_pages


class OcrWorkerService:
    """OCR-only application service used by an independent Worker process."""

    def __init__(
        self,
        *,
        storage: ObjectStorage,
        inference_service: InferenceService | Any | None = None,
        max_attachment_bytes: int | None = None,
        max_pages: int | None = None,
    ) -> None:
        self.storage = storage
        self.inference_service = inference_service or InferenceService()
        self.max_attachment_bytes = max_attachment_bytes or int(os.getenv("OCR_MAX_ATTACHMENT_BYTES", str(20 * 1024 * 1024)))
        self.max_pages = max_pages or int(os.getenv("OCR_MAX_PAGES", "20"))

    def process_command(self, command: OcrCommandV1) -> OcrResultEventV1:
        started = datetime.now(timezone.utc)
        try:
            content = self.storage.get_bytes(command.object_key)
            if len(content) > self.max_attachment_bytes:
                raise PermanentWorkerError("ATTACHMENT_TOO_LARGE", "attachment exceeds configured size limit")
            actual_sha = sha256_hex(content)
            if actual_sha != command.content_sha256:
                raise PermanentWorkerError("SHA_MISMATCH", "attachment checksum does not match command")

            filename = PurePosixPath(command.object_key).name or f"{command.attachment_id}.bin"
            content_type = "application/pdf" if filename.lower().endswith(".pdf") else "image/*"
            pages = expand_document_pages(content, filename=filename, content_type=content_type)
            if len(pages) > self.max_pages:
                raise PermanentWorkerError("PDF_PAGE_LIMIT", "document exceeds configured page limit")

            page_results: list[dict[str, Any]] = []
            for page in pages:
                analysis = self.inference_service.run(
                    plugin_name=command.plugin_name,
                    image=page.content,
                    filename=page.filename or filename,
                    source_kind="ocr_worker",
                )
                page_results.append({"page_number": page.page_number, "page_count": page.page_count, "analysis": analysis.get("analysis", analysis)})

            result_payload = {
                "schema_version": "1.0",
                "job_id": command.job_id,
                "request_id": command.request_id,
                "attachment_id": command.attachment_id,
                "plugin_name": command.plugin_name,
                "pipeline_profile": command.pipeline_profile,
                "ocr_profile_snapshot_id": command.ocr_profile_snapshot_id,
                "source_object_key": command.object_key,
                "content_sha256": actual_sha,
                "page_count": len(page_results),
                "pages": page_results,
            }
            result_bytes = json.dumps(result_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            result_key = f"ocr-results/{command.job_id}.json"
            stored = self.storage.put_bytes(result_key, result_bytes, content_type="application/json")
            completed = datetime.now(timezone.utc)
            return OcrResultEventV1(
                event_id=f"{command.job_id}:result:{command.attempt}",
                causation_id=command.command_id,
                job_id=command.job_id,
                request_id=command.request_id,
                attachment_id=command.attachment_id,
                status="SUCCEEDED",
                result_object_key=stored.object_key,
                result_sha256=stored.content_sha256,
                page_count=len(page_results),
                engine_version="id-doc-ocr",
                pipeline_profile=command.pipeline_profile,
                ocr_profile_snapshot_id=command.ocr_profile_snapshot_id,
                started_at=started,
                completed_at=completed,
                trace_id=command.trace_id,
            )
        except PermanentWorkerError as exc:
            return self._failed_event(command, started, exc.code, str(exc), retryable=False, category="PERMANENT")
        except Exception as exc:
            return self._failed_event(command, started, "OCR_WORKER_ERROR", f"{exc.__class__.__name__}: {exc}", retryable=True, category="TRANSIENT")

    def _failed_event(
        self,
        command: OcrCommandV1,
        started: datetime,
        code: str,
        message: str,
        *,
        retryable: bool,
        category: str,
    ) -> OcrResultEventV1:
        return OcrResultEventV1(
            event_id=f"{command.job_id}:failed:{command.attempt}",
            causation_id=command.command_id,
            job_id=command.job_id,
            request_id=command.request_id,
            attachment_id=command.attachment_id,
            status="FAILED",
            engine_version="id-doc-ocr",
            pipeline_profile=command.pipeline_profile,
            ocr_profile_snapshot_id=command.ocr_profile_snapshot_id,
            started_at=started,
            completed_at=datetime.now(timezone.utc),
            trace_id=command.trace_id,
            error_code=code,
            error_category=category,  # type: ignore[arg-type]
            retryable=retryable,
            safe_error_message=message,
        )


class PermanentWorkerError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code

