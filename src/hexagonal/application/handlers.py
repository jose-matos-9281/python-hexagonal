import logging
from typing import Any, Generic, Iterable

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
    IEventBus,
    IMessageHandler,
    IQueryBus,
    IQueryHandler,
    ISearchRepository,
    IUnitOfWork,
    IUseCase,
    TManager,
    TRepository,
)

logger = logging.getLogger(__name__)


class MessageHandler(
    IMessageHandler[TMessagePayloadType], Generic[TMessagePayloadType, TRepository]
):
    event_bus: IEventBus[Any]
    uow: IUnitOfWork[Any]

    def __init__(
        self,
        event_bus: IEventBus[TManager],
        uow: IUnitOfWork[TManager],
        repository: TRepository | None = None,
        query_bus: IQueryBus[TManager] | None = None,
        *repositories: TRepository,
    ) -> None:
        self.event_bus = event_bus
        self.uow = uow
        self._repository = repository
        self._query_bus = query_bus
        if repository is not None:
            self.uow.attach_repo(repository)
        for repository in repositories:
            self.uow.attach_repo(repository)

    @property
    def repository(self) -> TRepository:
        if self._repository is None:
            raise ValueError("Repository not provided")
        return self._repository

    @property
    def query_bus(self) -> IQueryBus[Any]:
        if self._query_bus is None:
            raise ValueError("Query bus not provided")
        return self._query_bus

    def handle_message(self, message: CloudMessage[TMessagePayloadType]) -> None:
        use_case = self.get_use_case(message.payload)
        with self.uow:
            events = use_case.execute()
            if not events:
                return
            messages = [message.derive(event, **message.metadata) for event in events]
            self.event_bus.outbox_repository.save(*messages)
        return self.event_bus.publish_from_outbox()


class EventHandlerBase(MessageHandler[TEvent, TRepository]):
    class UseCaseImpl(IUseCase):
        def __init__(
            self,
            event_handler: "EventHandlerBase[TEvent, TRepository]",
            event: TEvent,
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


class CommandHandlerBase(MessageHandler[TCommand, TRepository]):
    def execute(self, command: TCommand) -> Iterable[TEvento]:
        return []

    class UseCaseImpl(IUseCase):
        def __init__(
            self,
            command_handler: "CommandHandlerBase[TCommand, TRepository]",
            command: TCommand,
        ) -> None:
            self.command_handler = command_handler
            self.command = command

        def execute(self):
            evento = self.command_handler.execute(self.command)
            return evento

    def get_use_case(self, message: TCommand) -> IUseCase:
        return self.UseCaseImpl(self, message)


EventHandler = EventHandlerBase[TEvent, Any]
CommandHandler = CommandHandlerBase[TCommand, Any]


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
