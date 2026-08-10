from __future__ import annotations

from collections import Counter
from threading import Lock


class AsyncMetrics:
    """Small dependency-free metrics port; replace with OpenTelemetry exporter when enabled."""
    def __init__(self) -> None:
        self._values: Counter[str] = Counter()
        self._lock = Lock()

    def inc(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._values[name] += value

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._values)


metrics = AsyncMetrics()
