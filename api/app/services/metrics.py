from __future__ import annotations

import threading
from collections import defaultdict
from typing import Dict


class MetricsService:
    _instance: "MetricsService" | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "MetricsService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value

    def get_counter(self, name: str) -> int:
        with self._lock:
            return self._counters[name]

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def get_gauge(self, name: str) -> float:
        with self._lock:
            return self._gauges.get(name, 0.0)

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            data = {**self._counters, **self._gauges}
        return data
