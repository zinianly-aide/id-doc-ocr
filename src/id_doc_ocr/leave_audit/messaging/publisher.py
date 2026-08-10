from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings
from id_doc_ocr.leave_audit.messaging.topology import RabbitTopology


@dataclass(frozen=True, slots=True)
class PublishedMessage:
    exchange: str
    routing_key: str
    body: dict[str, Any]
    headers: dict[str, Any] = field(default_factory=dict)


class InMemoryPublisher:
    """Deterministic publisher used by unit tests and local dry runs."""

    def __init__(self) -> None:
        self.messages: list[PublishedMessage] = []

    def publish(self, *, exchange: str, routing_key: str, body: dict[str, Any], headers: dict[str, Any] | None = None) -> None:
        self.messages.append(PublishedMessage(exchange, routing_key, dict(body), dict(headers or {})))


class RabbitMqPublisher:
    """Synchronous pika publisher with publisher confirms and durable messages."""

    def __init__(self, settings: RabbitMQSettings | None = None) -> None:
        self.settings = settings or RabbitMQSettings.from_env()
        self._connection: Any = None
        self._channel: Any = None

    def connect(self) -> None:
        try:
            import pika
        except ImportError as exc:  # pragma: no cover - optional runtime dependency
            raise RuntimeError("RabbitMQ support requires the 'rabbitmq' extra") from exc
        parameters = pika.URLParameters(self.settings.url)
        parameters.virtual_host = self.settings.vhost
        if self.settings.tls:
            parameters.ssl_options = pika.SSLOptions()
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        RabbitTopology(self.settings).declare(self._channel)
        self._channel.confirm_delivery()

    def publish(self, *, exchange: str, routing_key: str, body: dict[str, Any], headers: dict[str, Any] | None = None) -> None:
        if self._channel is None or self._channel.is_closed:
            self.connect()
        import pika  # type: ignore[import-not-found]

        properties = pika.BasicProperties(
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=2,
            message_id=str(body.get("event_id") or body.get("command_id") or ""),
            headers={"schema_version": body.get("schema_version", "1.0"), **(headers or {})},
        )
        confirmed = self._channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            properties=properties,
        )
        if confirmed is False:
            raise RuntimeError("RabbitMQ publisher confirm was negative")

    def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            self._connection.close()

