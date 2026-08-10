from datetime import datetime, timezone

from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings
from id_doc_ocr.leave_audit.messaging.outbox import OutboxPublisher, TaskOutboxService
from id_doc_ocr.leave_audit.messaging.publisher import InMemoryPublisher
from id_doc_ocr.leave_audit.messaging.topology import RabbitTopology
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


class FakeChannel:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def exchange_declare(self, **kwargs):
        self.calls.append(("exchange_declare", kwargs))

    def queue_declare(self, **kwargs):
        self.calls.append(("queue_declare", kwargs))

    def queue_bind(self, **kwargs):
        self.calls.append(("queue_bind", kwargs))


def test_topology_declares_durable_queues_and_production_quorum_options():
    channel = FakeChannel()
    settings = RabbitMQSettings(quorum_queues=True, max_attempts=3)
    RabbitTopology(settings).declare(channel)

    queue_calls = [kwargs for name, kwargs in channel.calls if name == "queue_declare"]
    assert any(call["queue"] == settings.command_queue for call in queue_calls)
    command = next(call for call in queue_calls if call["queue"] == settings.command_queue)
    assert command["arguments"]["x-queue-type"] == "quorum"
    assert command["arguments"]["x-delivery-limit"] == 3


def test_task_outbox_preserves_command_id_and_publishes_with_confirm_semantics(tmp_path):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    service = TaskOutboxService(repo, RabbitMQSettings())
    event = service.enqueue_ocr_command(
        request_id="LV-1",
        job_id="JOB-1",
        attachment_id="ATT-1",
        object_key="attachments/att-1.pdf",
        content_sha256="a" * 64,
        plugin_name="diagnosis_proof",
        pipeline_profile="production-v1",
        ocr_profile_snapshot_id="ocr-cfg-1",
        trace_id="trace-1",
        command_id="CMD-1",
    )
    publisher = InMemoryPublisher()
    assert OutboxPublisher(repo, publisher, RabbitMQSettings()).publish_pending() == 1
    assert publisher.messages[0].body["command_id"] == "CMD-1"
    assert repo.list_pending_outbox() == []
    assert event.event_id == "CMD-1"


def test_outbox_failed_publish_is_retryable_and_keeps_event(tmp_path):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    service = TaskOutboxService(repo)
    service.enqueue_ocr_command(
        request_id="LV-1",
        job_id="JOB-1",
        attachment_id="ATT-1",
        object_key="attachments/att-1.pdf",
        content_sha256="b" * 64,
        plugin_name="diagnosis_proof",
        pipeline_profile="production-v1",
        ocr_profile_snapshot_id="ocr-cfg-1",
        trace_id="trace-1",
    )

    class FailingPublisher:
        def publish(self, **kwargs):
            raise TimeoutError("rabbit unavailable")

    assert OutboxPublisher(repo, FailingPublisher()).publish_pending() == 0
    pending = repo.list_pending_outbox()
    assert len(pending) == 1
    assert pending[0].attempt_count == 1
    assert "rabbit unavailable" in (pending[0].last_error or "")
