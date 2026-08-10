from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from id_doc_ocr.leave_audit.messaging.config import RabbitMQSettings


@dataclass(frozen=True, slots=True)
class RabbitTopology:
    settings: RabbitMQSettings

    def declare(self, channel: Any) -> None:
        """Declare durable exchanges/queues and bounded retry routes.

        The channel is intentionally duck-typed so topology can be tested
        without a RabbitMQ daemon and used with pika BlockingChannel.
        """

        s = self.settings
        channel.exchange_declare(exchange=s.commands_exchange, exchange_type="direct", durable=True)
        channel.exchange_declare(exchange=s.events_exchange, exchange_type="topic", durable=True)
        channel.exchange_declare(exchange=s.retry_exchange, exchange_type="direct", durable=True)
        channel.exchange_declare(exchange=s.dead_letter_exchange, exchange_type="direct", durable=True)

        self._queue(channel, s.command_queue)
        self._queue(channel, s.result_queue)
        self._queue(channel, s.dead_letter_queue)
        self._queue(channel, s.retry_30s_queue, ttl=30_000)
        self._queue(channel, s.retry_5m_queue, ttl=300_000)
        self._queue(channel, s.retry_30m_queue, ttl=1_800_000)

        channel.queue_bind(queue=s.command_queue, exchange=s.commands_exchange, routing_key=s.command_routing_key)
        channel.queue_bind(queue=s.result_queue, exchange=s.events_exchange, routing_key="ocr.completed.v1")
        channel.queue_bind(queue=s.result_queue, exchange=s.events_exchange, routing_key="ocr.failed.v1")
        channel.queue_bind(queue=s.dead_letter_queue, exchange=s.dead_letter_exchange, routing_key="ocr.execute.dead")

        channel.queue_bind(queue=s.retry_30s_queue, exchange=s.retry_exchange, routing_key="ocr.execute.retry.30s")
        channel.queue_bind(queue=s.retry_5m_queue, exchange=s.retry_exchange, routing_key="ocr.execute.retry.5m")
        channel.queue_bind(queue=s.retry_30m_queue, exchange=s.retry_exchange, routing_key="ocr.execute.retry.30m")

    def _queue(self, channel: Any, name: str, ttl: int | None = None) -> None:
        arguments: dict[str, Any] = {}
        if self.settings.quorum_queues:
            arguments["x-queue-type"] = "quorum"
            if name == self.settings.command_queue:
                arguments["x-delivery-limit"] = self.settings.max_attempts
        if ttl is not None:
            arguments["x-message-ttl"] = ttl
            arguments["x-dead-letter-exchange"] = self.settings.commands_exchange
            arguments["x-dead-letter-routing-key"] = self.settings.command_routing_key
        channel.queue_declare(queue=name, durable=True, arguments=arguments)

