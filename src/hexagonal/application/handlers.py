import logging
from typing import Any, Iterable

from hexagonal.domain import (
    CloudMessage,
    QueryResults,
    TCommand,
    TEvent,
    TEvento,
    TMessagePayloadType,
    TQuery,
    TView,
)
from hexagonal.ports.drivens import (
    IBaseRepository,
    IEventBus,
    IMessageHandler,
    IQueryHandler,
    ISearchRepository,
    IUnitOfWork,
    IUseCase,
    TManager,
)

logger = logging.getLogger(__name__)


class MessageHandler(IMessageHandler[TMessagePayloadType]):
    event_bus: IEventBus[Any]
    uow: IUnitOfWork[Any]

    def __init__(
        self,
        event_bus: IEventBus[TManager],
        uow: IUnitOfWork[TManager],
        *repositories: IBaseRepository[TManager],
    ) -> None:
        self.event_bus = event_bus
        self.uow = uow
        for repository in repositories:
            self.uow.attach_repo(repository)

    def handle_message(self, message: CloudMessage[TMessagePayloadType]) -> None:
        use_case = self.get_use_case(message.payload)
        with self.uow:
            events = use_case.execute()
            if not events:
                return
            messages = [message.derive(event, **message.metadata) for event in events]
            self.event_bus.outbox_repository.save(*messages)
        return self.event_bus.publish_from_outbox()


class EventHandler(MessageHandler[TEvent]):
    class UseCaseImpl(IUseCase):
        def __init__(
            self, event_handler: "EventHandler[TEvent]", event: TEvent
        ) -> None:
            self.event_handler = event_handler
            self.event = event

        def execute(self):
            evento = self.event_handler.handle(self.event)
            return evento

    def handle(self, event: TEvent) -> Iterable[TEvento]:
        return []

    def get_use_case(self, message: TEvent) -> IUseCase:
        return self.UseCaseImpl(self, message)


class CommandHandler(MessageHandler[TCommand]):
    def execute(self, command: TCommand) -> Iterable[TEvento]:
        return []

    class UseCaseImpl(IUseCase):
        def __init__(
            self, event_handler: "CommandHandler[TCommand]", event: TCommand
        ) -> None:
            self.event_handler = event_handler
            self.event = event

        def execute(self):
            evento = self.event_handler.execute(self.event)
            return evento

    def get_use_case(self, message: TCommand) -> IUseCase:
        return self.UseCaseImpl(self, message)


class QueryHandler(IQueryHandler[TManager, TQuery, TView]):
    def __init__(
        self,
        repository: ISearchRepository[TManager, TQuery, TView],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._repository = repository

    @property
    def repository(self) -> ISearchRepository[TManager, TQuery, TView]:
        return self._repository

    def get(self, query: TQuery) -> QueryResults[TView]:
        results = self.repository.search(query)
        return QueryResults[TView].new(items=results, limit=len(results))
