import threading
from abc import abstractmethod
from typing import Any, Callable

from hexagonal.application import Infrastructure
from hexagonal.domain import CloudMessage
from hexagonal.ports.drivens import (
    IBaseMessageBus,
    IInboxRepository,
    IOutboxRepository,
    TManager,
)
from hexagonal.ports.drivens.scoped import IWriteScopeRunner, TWriteScope


class MessageBus(IBaseMessageBus[TManager], Infrastructure):
    def __init__(
        self,
        inbox_repository: IInboxRepository[TManager],
        outbox_repository: IOutboxRepository[TManager],
    ) -> None:
        self._inbox_repository = inbox_repository
        self._outbox_repository = outbox_repository
        self._write_scope_runner: IWriteScopeRunner[Any] | None = None
        self._outbox_repository_getter: (
            Callable[[Any], IOutboxRepository[TManager]] | None
        ) = None
        self._outbox_publish_lock = threading.RLock()
        super().__init__()

    @property
    def inbox_repository(self) -> IInboxRepository[TManager]:
        return self._inbox_repository

    @property
    def outbox_repository(self) -> IOutboxRepository[TManager]:
        return self._outbox_repository

    def configure_scope_runtime(
        self,
        *,
        write_scope_runner: IWriteScopeRunner[TWriteScope] | None = None,
        outbox_repository_getter: Callable[[TWriteScope], IOutboxRepository[TManager]]
        | None = None,
    ) -> None:
        self._write_scope_runner = write_scope_runner
        self._outbox_repository_getter = outbox_repository_getter

    def save_to_outbox(self, *messages: CloudMessage[Any]) -> None:
        self.verify()
        self._run_with_outbox_repository(
            lambda outbox_repository: outbox_repository.save(*messages)
        )

    # publish
    def publish_from_outbox(self, limit: int | None = None) -> None:
        self.verify()
        with self._outbox_publish_lock:
            self._run_with_outbox_repository(
                lambda outbox_repository: self._publish_messages(
                    outbox_repository,
                    *outbox_repository.fetch_pending(limit=limit),
                )
            )

    def _run_with_outbox_repository(
        self,
        work: Callable[[IOutboxRepository[TManager]], Any],
    ) -> Any:
        if self._write_scope_runner is None or self._outbox_repository_getter is None:
            return work(self.outbox_repository)

        outbox_repository_getter = self._outbox_repository_getter
        scope = self._write_scope_runner.current_write_scope
        if scope is not None:
            return work(outbox_repository_getter(scope))

        return self._write_scope_runner.run_in_write_scope(
            lambda write_scope: work(outbox_repository_getter(write_scope))
        )

    def _publish_messages(
        self,
        outbox_repository: IOutboxRepository[TManager],
        *messages: CloudMessage[Any],
    ) -> None:
        for message in messages:
            try:
                self._publish_message(message)
                outbox_repository.mark_as_published(message.message_id)
            except Exception as e:
                outbox_repository.mark_as_failed(message.message_id, error=str(e))

    @abstractmethod
    def _publish_message(self, message: CloudMessage[Any]) -> None: ...

    # consume
    def _process_messages(self, *messages: CloudMessage[Any]) -> None:
        handlers: list[tuple[CloudMessage[Any], str]] = []
        for msg in messages:
            handlers.extend((msg, handler) for handler in self._get_handlers(msg))
        for msg, handler in handlers:
            self._process_message(msg, handler)

    def _process_message(self, message: CloudMessage[Any], handler: str) -> None:
        duplicated = self.inbox_repository.register_message(message, handler)
        if not duplicated:
            try:
                self._handle_message(message, handler)
                self.inbox_repository.mark_as_processed(message.message_id, handler)
            except Exception as e:
                self.inbox_repository.mark_as_failed(
                    message.message_id, handler, error=str(e)
                )
                raise

    @abstractmethod
    def _get_handlers(self, message: CloudMessage[Any]) -> list[str]: ...

    @abstractmethod
    def _handle_message(self, message: CloudMessage[Any], handler: str) -> None: ...
