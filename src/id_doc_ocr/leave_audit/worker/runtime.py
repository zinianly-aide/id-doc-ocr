from __future__ import annotations

import json
from typing import Any

from id_doc_ocr.leave_audit.contracts.ocr import OcrCommandV1
from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings
from id_doc_ocr.leave_audit.messaging.publisher import RabbitMqPublisher
from id_doc_ocr.leave_audit.messaging.topology import RabbitTopology
from id_doc_ocr.leave_audit.storage.base import ObjectStorage
from id_doc_ocr.leave_audit.storage.factory import create_object_storage
from id_doc_ocr.leave_audit.worker.ocr_worker import OcrWorkerService


class OcrWorkerRuntime:
    """RabbitMQ consumer enforcing validate -> publish -> ACK ordering."""

    def __init__(
        self,
        *,
        service: OcrWorkerService,
        publisher: RabbitMqPublisher,
        settings: RabbitMQSettings | None = None,
    ) -> None:
        self.service = service
        self.publisher = publisher
        self.settings = settings or RabbitMQSettings.from_env()

    def run_forever(self) -> None:  # pragma: no cover - requires RabbitMQ
        try:
            import pika
        except ImportError as exc:
            raise RuntimeError("RabbitMQ support requires the 'rabbitmq' extra") from exc
        parameters = pika.URLParameters(self.settings.url)
        parameters.virtual_host = self.settings.vhost
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        RabbitTopology(self.settings).declare(channel)
        channel.basic_qos(prefetch_count=self.settings.prefetch)
        channel.basic_consume(queue=self.settings.command_queue, on_message_callback=self.handle_delivery, auto_ack=False)
        channel.start_consuming()

    def handle_delivery(self, channel: Any, method: Any, properties: Any, body: bytes) -> None:
        try:
            command = OcrCommandV1.model_validate_json(body)
        except Exception:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        event = self.service.process_command(command)
        if event.status == "FAILED" and event.retryable and command.attempt < self.settings.max_attempts:
            retry_command = command.model_copy(update={"attempt": command.attempt + 1})
            self.publisher.publish(
                exchange=self.settings.retry_exchange,
                routing_key=self.retry_routing_key(command.attempt + 1),
                body=retry_command.model_dump(mode="json"),
                headers={"event_type": "ocr.execute.retry", "attempt": command.attempt + 1},
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        routing_key = self.settings.completed_routing_key if event.status == "SUCCEEDED" else self.settings.failed_routing_key
        self.publisher.publish(
            exchange=self.settings.events_exchange,
            routing_key=routing_key,
            body=event.model_dump(mode="json"),
            headers={"event_type": routing_key},
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)

    @staticmethod
    def retry_routing_key(attempt: int) -> str:
        if attempt <= 1:
            return "ocr.execute.retry.30s"
        if attempt == 2:
            return "ocr.execute.retry.5m"
        return "ocr.execute.retry.30m"


def build_default_runtime(settings: RabbitMQSettings | None = None) -> OcrWorkerRuntime:
    effective = settings or RabbitMQSettings.from_env()
    return OcrWorkerRuntime(
        service=OcrWorkerService(storage=create_object_storage()),
        publisher=RabbitMqPublisher(effective),
        settings=effective,
    )
