from abc import abstractmethod
from typing import Any

from hexagonal.application import Infrastructure
from hexagonal.domain import CloudMessage
from hexagonal.ports.drivens import (
    IBaseMessageBus,
    IInboxRepository,
    IOutboxRepository,
    TManager,
)


class MessageBus(IBaseMessageBus[TManager], Infrastructure):
    def __init__(
        self,
        inbox_repository: IInboxRepository[TManager],
        outbox_repository: IOutboxRepository[TManager],
    ):
        self._inbox_repository = inbox_repository
        self._outbox_repository = outbox_repository
        super().__init__()

    @property
    def inbox_repository(self) -> IInboxRepository[TManager]:
        return self._inbox_repository

    @property
    def outbox_repository(self) -> IOutboxRepository[TManager]:
        return self._outbox_repository

    # publish
    def publish_from_outbox(self, limit: int | None = None):
        self.verify()
        messages = self.outbox_repository.fetch_pending(limit=limit)
        self._publish_messages(*messages)

    def _publish_messages(self, *messages: CloudMessage[Any]) -> None:
        for message in messages:
            try:
                self._publish_message(message)
                self.outbox_repository.mark_as_published(message.message_id)
            except Exception as e:
                self.outbox_repository.mark_as_failed(message.message_id, error=str(e))

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
