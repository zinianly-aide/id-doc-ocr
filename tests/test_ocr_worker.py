from pathlib import Path

from id_doc_ocr.leave_audit.contracts.ocr import OcrCommandV1
from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings
from id_doc_ocr.leave_audit.storage.local import LocalObjectStorage
from id_doc_ocr.leave_audit.storage.base import sha256_hex
from id_doc_ocr.leave_audit.worker.ocr_worker import OcrWorkerService
from id_doc_ocr.leave_audit.worker.runtime import OcrWorkerRuntime


class FakeInference:
    def run(self, **kwargs):
        return {"analysis": {"extracted_fields": [{"name": "patient_name", "value": "张三"}]}}


def command(content: bytes) -> OcrCommandV1:
    return OcrCommandV1(
        command_id="cmd-1",
        job_id="job-1",
        request_id="LV-1",
        attachment_id="att-1",
        object_key="attachments/att-1.png",
        content_sha256=sha256_hex(content),
        plugin_name="diagnosis_proof",
        pipeline_profile="production-v1",
        ocr_profile_snapshot_id="ocr-cfg-1",
        trace_id="trace-1",
        created_at="2026-08-11T00:00:00Z",
    )


def test_worker_writes_full_analysis_to_object_storage_and_returns_small_event(tmp_path):
    storage = LocalObjectStorage(tmp_path / "objects")
    content = b"not-a-real-image-but-mock-backbone-input"
    storage.put_bytes("attachments/att-1.png", content, content_type="image/png")
    worker = OcrWorkerService(storage=storage, inference_service=FakeInference())

    event = worker.process_command(command(content))

    assert event.status == "SUCCEEDED"
    assert event.result_object_key == "ocr-results/job-1.json"
    result = storage.get_bytes(event.result_object_key)
    assert b"patient_name" in result
    assert event.result_sha256 == sha256_hex(result)


def test_worker_sha_mismatch_is_permanent_failure(tmp_path):
    storage = LocalObjectStorage(tmp_path / "objects")
    storage.put_bytes("attachments/att-1.png", b"actual")
    bad = command(b"expected").model_copy(update={"content_sha256": "a" * 64})
    event = OcrWorkerService(storage=storage, inference_service=FakeInference()).process_command(bad)

    assert event.status == "FAILED"
    assert event.error_code == "SHA_MISMATCH"
    assert event.error_category == "PERMANENT"
    assert event.retryable is False


def test_local_object_storage_rejects_path_traversal(tmp_path):
    storage = LocalObjectStorage(tmp_path / "objects")
    try:
        storage.put_bytes("../../outside", b"secret")
    except ValueError as exc:
        assert "escapes" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("path traversal must be rejected")


def test_runtime_retry_routes_are_bounded():
    assert OcrWorkerRuntime.retry_routing_key(1) == "ocr.execute.retry.30s"
    assert OcrWorkerRuntime.retry_routing_key(2) == "ocr.execute.retry.5m"
    assert OcrWorkerRuntime.retry_routing_key(3) == "ocr.execute.retry.30m"
    assert OcrWorkerRuntime.retry_routing_key(99) == "ocr.execute.retry.30m"
