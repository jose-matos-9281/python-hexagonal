# pyright: reportMissingParameterType=none, reportGeneralTypeIssues=none

import logging
import threading
from queue import Empty, Queue
from typing import Any, Mapping

from hexagonal.adapters.drivens.buses.base import BaseCommandBus
from hexagonal.domain import CloudMessage, TCommand
from hexagonal.ports.drivens import TManager

logger = logging.getLogger(__name__)


class InMemoryCommandBus(BaseCommandBus[TManager]):
    def _publish_message(self, message: CloudMessage[TCommand]) -> None:
        return self._process_messages(message)

    def consume(self, limit: int | None = None):
        return  # No-op for non-queued bus


class InMemoryQueueCommandBus(BaseCommandBus[TManager]):
    def initialize(self, env: Mapping[str, str]) -> None:
        self.queue: Queue[CloudMessage[Any]] = Queue()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)

        super().initialize(env)

    def shutdown(self) -> None:
        # Si tienes lifecycle, llama esto al apagar la app
        self._stop.set()
        self._worker.join(timeout=5)

    def _publish_message(self, message: CloudMessage[TCommand]) -> None:
        self.verify()
        self.queue.put(
            message
        )  # bloquea si hubiera maxsize; puedes usar put_nowait si quieres
        logger.debug(
            "Enqueued command: %s | %s | %s | %s",
            message.message_id,
            message.causation_id,
            message.correlation_id,
            message.type,
        )
        # No llamamos consume() aquí. El worker ya está drenando.

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                message = self.queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                logger.debug(
                    "Processing command: %s | %s | %s | %s",
                    message.message_id,
                    message.causation_id,
                    message.correlation_id,
                    message.type,
                )
                self.dispatch(message)
            finally:
                self.queue.task_done()

    def consume(self, limit: int | None = None):
        self._worker.start()
