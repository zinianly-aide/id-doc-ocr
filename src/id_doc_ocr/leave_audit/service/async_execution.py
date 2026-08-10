from __future__ import annotations

import uuid

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.async_status import OcrJobStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditTask
from id_doc_ocr.leave_audit.messaging.outbox import TaskOutboxService
from id_doc_ocr.leave_audit.repository.base import LeaveAuditRepository
from id_doc_ocr.leave_audit.storage.base import ObjectStorage, sha256_hex


class AsyncExecutionService:
    def __init__(self, repository: LeaveAuditRepository, adapter: LeaveSystemAdapter, storage: ObjectStorage) -> None:
        self.repository = repository
        self.adapter = adapter
        self.storage = storage

    def queue_task(self, task: LeaveAuditTask, *, trace_id: str | None = None) -> list[str]:
        if not task.attachments:
            raise ValueError("task has no attachments")
        profile = task.ocr_profile_snapshot_id or "ocr-default-v1"
        task.ocr_profile_snapshot_id = profile
        task.ocr_status = OcrJobStatus.QUEUED
        task.status = task.status
        self.repository.save_task(task)
        outbox = TaskOutboxService(self.repository)
        jobs: list[str] = []
        for attachment in task.attachments:
            payload = self.adapter.download_attachment(attachment.attachment_url)
            object_key = str(attachment.metadata.get("object_key") or f"leave-audit/{task.request_id}/{attachment.attachment_id}")
            stored = self.storage.put_bytes(object_key, payload, content_type=attachment.content_type)
            attachment.metadata["object_key"] = stored.object_key
            attachment.metadata["content_sha256"] = sha256_hex(payload)
            job_id = str(uuid.uuid4())
            jobs.append(job_id)
            outbox.enqueue_ocr_command(request_id=task.request_id, job_id=job_id, attachment_id=attachment.attachment_id,
                                       object_key=stored.object_key, content_sha256=stored.content_sha256,
                                       plugin_name=attachment.plugin_name or "diagnosis_proof", pipeline_profile="production-v1",
                                       ocr_profile_snapshot_id=profile, trace_id=trace_id or task.request_id)
        self.repository.save_task(task)
        return jobs
