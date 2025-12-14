# pyright: reportMissingParameterType=none, reportGeneralTypeIssues=none, reportUnknownMemberType=none

import logging
import threading
from queue import Empty, Queue
from typing import Mapping

from hexagonal.adapters.drivens.buses.base import BaseEventBus
from hexagonal.domain import CloudMessage, TEvent, TEvento
from hexagonal.ports.drivens import TManager

logger = logging.getLogger(__name__)


class InMemoryEventBus(BaseEventBus[TManager]):
    def _publish_message(self, message: CloudMessage[TEvento]) -> None:
        super()._publish_message(message)
        self._process_messages(message)

    def publish(self, *events: CloudMessage[TEvent]) -> None:
        return self._publish_messages(*events)

    def consume(self, limit: int | None = None):
        pass  # No-op for non-queued bus


class InMemoryQueueEventBus(BaseEventBus[TManager]):
    def initialize(self, env: Mapping[str, str]) -> None:
        self.queue: Queue[CloudMessage[TEvento]] = Queue()  # o Queue(maxsize=...)
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)

        super().initialize(env)

    def shutdown(self) -> None:
        # Llamar en el lifecycle de tu app
        self._stop.set()
        self._worker.join(timeout=5)

    def publish(self, *events: CloudMessage[TEvent]) -> None:
        return self._publish_messages(*events)

    def _publish_message(self, message: CloudMessage[TEvento]) -> None:
        super()._publish_message(message)
        self.verify()
        self.queue.put(message)
        # No llamamos consume() aquí: el worker se encarga.

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                event = self.queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                logger.debug(
                    "Processing event: %s | %s | %s | %s",
                    event.message_id,
                    event.causation_id,
                    event.correlation_id,
                    event.type,
                )
                self._process_messages(event)
            finally:
                self.queue.task_done()

    def consume(self, limit: int | None = None):
        self._worker.start()
