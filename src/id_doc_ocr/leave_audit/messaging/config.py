from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class RabbitMQSettings:
    url: str = "amqp://guest:guest@127.0.0.1:5672/"
    vhost: str = "/"
    commands_exchange: str = "leave.audit.commands"
    events_exchange: str = "leave.audit.events"
    retry_exchange: str = "leave.audit.retry"
    dead_letter_exchange: str = "leave.audit.dlx"
    command_queue: str = "ocr.execute.v1.q"
    result_queue: str = "leave.audit.results.v1.q"
    retry_30s_queue: str = "ocr.execute.retry.30s.q"
    retry_5m_queue: str = "ocr.execute.retry.5m.q"
    retry_30m_queue: str = "ocr.execute.retry.30m.q"
    dead_letter_queue: str = "ocr.execute.dlq"
    command_routing_key: str = "ocr.execute.v1"
    completed_routing_key: str = "ocr.completed.v1"
    failed_routing_key: str = "ocr.failed.v1"
    prefetch: int = 1
    quorum_queues: bool = False
    tls: bool = False
    max_attempts: int = 3

    @classmethod
    def from_env(cls) -> "RabbitMQSettings":
        defaults = cls()
        return cls(
            url=os.getenv("RABBITMQ_URL", defaults.url),
            vhost=os.getenv("RABBITMQ_VHOST", defaults.vhost),
            commands_exchange=os.getenv("RABBITMQ_COMMANDS_EXCHANGE", defaults.commands_exchange),
            events_exchange=os.getenv("RABBITMQ_EVENTS_EXCHANGE", defaults.events_exchange),
            retry_exchange=os.getenv("RABBITMQ_RETRY_EXCHANGE", defaults.retry_exchange),
            dead_letter_exchange=os.getenv("RABBITMQ_DLX", defaults.dead_letter_exchange),
            command_queue=os.getenv("RABBITMQ_COMMAND_QUEUE", defaults.command_queue),
            result_queue=os.getenv("RABBITMQ_RESULT_QUEUE", defaults.result_queue),
            retry_30s_queue=os.getenv("RABBITMQ_RETRY_30S_QUEUE", defaults.retry_30s_queue),
            retry_5m_queue=os.getenv("RABBITMQ_RETRY_5M_QUEUE", defaults.retry_5m_queue),
            retry_30m_queue=os.getenv("RABBITMQ_RETRY_30M_QUEUE", defaults.retry_30m_queue),
            dead_letter_queue=os.getenv("RABBITMQ_DLQ", defaults.dead_letter_queue),
            command_routing_key=os.getenv("RABBITMQ_COMMAND_ROUTING_KEY", defaults.command_routing_key),
            completed_routing_key=os.getenv("RABBITMQ_COMPLETED_ROUTING_KEY", defaults.completed_routing_key),
            failed_routing_key=os.getenv("RABBITMQ_FAILED_ROUTING_KEY", defaults.failed_routing_key),
            prefetch=max(1, int(os.getenv("OCR_WORKER_PREFETCH", str(defaults.prefetch)))),
            quorum_queues=_env_bool("RABBITMQ_QUORUM_QUEUES", defaults.quorum_queues),
            tls=_env_bool("RABBITMQ_TLS", defaults.tls),
            max_attempts=max(1, int(os.getenv("OCR_MAX_ATTEMPTS", str(defaults.max_attempts)))),
        )
