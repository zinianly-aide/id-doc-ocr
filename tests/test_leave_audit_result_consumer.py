import hashlib
import json
from datetime import datetime, timezone

from id_doc_ocr.leave_audit.contracts.ocr import OcrResultEventV1
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.result_consumer import OcrResultConsumerService
from id_doc_ocr.leave_audit.storage.local import LocalObjectStorage
from id_doc_ocr.leave_audit.worker.callback import CallbackOutboxWorker


class Adapter:
    def __init__(self): self.calls = []
    def fetch_pending_attachments(self): return []
    def download_attachment(self, url): return b""
    def push_audit_result(self, result): self.calls.append(result)


def test_result_consumer_commits_and_deduplicates(tmp_path):
    repo = SQLiteRepository(tmp_path / "audit.db")
    task = LeaveAuditTask(request_id="LV-1", leave_type="SICK", employee_name="Alice", attachments=[LeaveAttachment("ATT-1", "fixture://a", plugin_name="diagnosis_proof")])
    repo.save_task(task)
    storage = LocalObjectStorage(tmp_path / "objects")
    payload = json.dumps({"pages": [{"analysis": {"extracted_fields": [{"name": "name", "value": "Alice"}]}}]}).encode()
    stored = storage.put_bytes("ocr-results/J1.json", payload)
    now = datetime.now(timezone.utc)
    event = OcrResultEventV1(event_id="E1", causation_id="C1", trace_id="T1", started_at=now, completed_at=now, job_id="J1", request_id="LV-1", attachment_id="ATT-1", status="SUCCEEDED", result_object_key=stored.object_key, result_sha256=hashlib.sha256(payload).hexdigest(), page_count=1, engine_version="test", pipeline_profile="test", ocr_profile_snapshot_id="ocr-v1")
    consumer = OcrResultConsumerService(repo, storage)
    assert consumer.handle_event(event) is True
    assert consumer.handle_event(event) is False
    assert len(repo.list_pending_callbacks()) == 1


def test_callback_worker_is_idempotent(tmp_path):
    repo = SQLiteRepository(tmp_path / "audit.db")
    task = LeaveAuditTask(request_id="LV-2", leave_type="SICK", employee_name="Alice", attachments=[LeaveAttachment("ATT-2", "fixture://a", plugin_name="diagnosis_proof")])
    repo.save_task(task)
    storage = LocalObjectStorage(tmp_path / "objects")
    payload = json.dumps({"pages": [{"analysis": {"extracted_fields": [{"name": "name", "value": "Alice"}]}}]}).encode()
    stored = storage.put_bytes("ocr-results/J2.json", payload)
    now = datetime.now(timezone.utc)
    event = OcrResultEventV1(event_id="E2", causation_id="C2", trace_id="T2", started_at=now, completed_at=now, job_id="J2", request_id="LV-2", attachment_id="ATT-2", status="SUCCEEDED", result_object_key=stored.object_key, result_sha256=hashlib.sha256(payload).hexdigest(), page_count=1, engine_version="test", pipeline_profile="test", ocr_profile_snapshot_id="ocr-v1")
    OcrResultConsumerService(repo, storage).handle_event(event)
    adapter = Adapter()
    worker = CallbackOutboxWorker(repo, adapter)
    assert worker.process_pending() == 1
    assert worker.process_pending() == 0
    assert len(adapter.calls) == 1
