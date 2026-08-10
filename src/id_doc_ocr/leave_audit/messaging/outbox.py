from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from id_doc_ocr.leave_audit.contracts.ocr import OcrCommandV1
from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings
from id_doc_ocr.leave_audit.messaging.publisher import InMemoryPublisher, RabbitMqPublisher


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class OutboxEvent:
    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=_now)
    published_at: str | None = None
    attempt_count: int = 0
    last_error: str | None = None


@dataclass(slots=True)
class CallbackOutboxItem:
    callback_id: str
    request_id: str
    decision_version: int
    payload: dict[str, Any]
    status: str = "PENDING"
    attempt_count: int = 0
    next_attempt_at: str | None = None
    last_error: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


class OutboxRepository(Protocol):
    def enqueue_outbox_event(self, event: OutboxEvent) -> None: ...
    def list_pending_outbox(self, limit: int = 100) -> list[OutboxEvent]: ...
    def mark_outbox_published(self, event_id: str) -> None: ...
    def mark_outbox_failed(self, event_id: str, error: str) -> None: ...


class TaskOutboxService:
    def __init__(self, repository: OutboxRepository, settings: RabbitMQSettings | None = None) -> None:
        self.repository = repository
        self.settings = settings or RabbitMQSettings.from_env()

    def enqueue_ocr_command(
        self,
        *,
        request_id: str,
        job_id: str,
        attachment_id: str,
        object_key: str,
        content_sha256: str,
        plugin_name: str,
        pipeline_profile: str,
        ocr_profile_snapshot_id: str,
        trace_id: str,
        command_id: str | None = None,
    ) -> OutboxEvent:
        command = OcrCommandV1(
            command_id=command_id or str(uuid.uuid4()),
            job_id=job_id,
            request_id=request_id,
            attachment_id=attachment_id,
            object_key=object_key,
            content_sha256=content_sha256,
            plugin_name=plugin_name,
            pipeline_profile=pipeline_profile,
            ocr_profile_snapshot_id=ocr_profile_snapshot_id,
            trace_id=trace_id,
            created_at=datetime.now(timezone.utc),
        )
        event = OutboxEvent(
            event_id=command.command_id,
            aggregate_type="ocr_job",
            aggregate_id=job_id,
            event_type="ocr.execute.v1",
            payload=command.model_dump(mode="json"),
        )
        self.repository.enqueue_outbox_event(event)
        return event


class OutboxPublisher:
    def __init__(self, repository: OutboxRepository, publisher: Any, settings: RabbitMQSettings | None = None) -> None:
        self.repository = repository
        self.publisher = publisher
        self.settings = settings or RabbitMQSettings.from_env()

    def publish_pending(self, limit: int = 100) -> int:
        published = 0
        for event in self.repository.list_pending_outbox(limit=limit):
            try:
                self.publisher.publish(
                    exchange=self.settings.commands_exchange,
                    routing_key=self.settings.command_routing_key,
                    body=event.payload,
                    headers={"event_type": event.event_type, "attempt": event.attempt_count + 1},
                )
            except Exception as exc:
                self.repository.mark_outbox_failed(event.event_id, f"{exc.__class__.__name__}: {exc}")
                continue
            self.repository.mark_outbox_published(event.event_id)
            published += 1
        return published
