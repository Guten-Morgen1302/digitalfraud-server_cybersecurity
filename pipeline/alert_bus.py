from __future__ import annotations

import asyncio
from typing import Any


class AlertBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._last_alerts: list[dict[str, Any]] = []

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    async def publish(self, alert: dict[str, Any]) -> None:
        self._last_alerts.insert(0, alert)
        self._last_alerts = self._last_alerts[:50]
        dead: list[asyncio.Queue[dict[str, Any]]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(alert)
            except asyncio.QueueFull:
                dead.append(queue)
        for queue in dead:
            self.unsubscribe(queue)

    def last_alerts(self) -> list[dict[str, Any]]:
        return list(self._last_alerts)


alert_bus = AlertBus()
