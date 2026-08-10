from __future__ import annotations

from typing import Any

from id_doc_ocr.leave_audit.contracts.ocr import OcrResultEventV1
from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings
from id_doc_ocr.leave_audit.messaging.topology import RabbitTopology
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.result_consumer import OcrResultConsumerService
from id_doc_ocr.leave_audit.storage.factory import create_object_storage


class OcrResultConsumerRuntime:
    def __init__(self, consumer: OcrResultConsumerService, settings: RabbitMQSettings | None = None) -> None:
        self.consumer = consumer
        self.settings = settings or RabbitMQSettings.from_env()

    def run_forever(self) -> None:  # pragma: no cover
        try:
            import pika
        except ImportError as exc:
            raise RuntimeError("RabbitMQ support requires the 'rabbitmq' extra") from exc
        connection = pika.BlockingConnection(pika.URLParameters(self.settings.url))
        channel = connection.channel()
        RabbitTopology(self.settings).declare(channel)
        channel.basic_qos(prefetch_count=self.settings.prefetch)
        channel.basic_consume(queue=self.settings.result_queue, on_message_callback=self.handle_delivery, auto_ack=False)
        channel.start_consuming()

    def handle_delivery(self, channel: Any, method: Any, properties: Any, body: bytes) -> None:
        try:
            event = OcrResultEventV1.model_validate_json(body)
            self.consumer.handle_event(event)
        except Exception:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        channel.basic_ack(delivery_tag=method.delivery_tag)


def build_default_result_runtime(settings: RabbitMQSettings | None = None) -> OcrResultConsumerRuntime:
    repository = SQLiteRepository()
    return OcrResultConsumerRuntime(OcrResultConsumerService(repository, create_object_storage()), settings)
