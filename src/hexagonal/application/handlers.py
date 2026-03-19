import logging
from typing import Any, Callable, Generic, Iterable, Protocol, TypeVar

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
    IReadScopeRunner,
    ISearchRepository,
    IUnitOfWork,
    IUseCase,
    TManager,
    TRepository,
    IWriteScopeRunner,
)

logger = logging.getLogger(__name__)

TWriteScope = TypeVar("TWriteScope")
TReadScope = TypeVar("TReadScope")
TWriteScope_contra = TypeVar("TWriteScope_contra", contravariant=True)


class IScopedMessageHandlerProvider(Protocol[TMessagePayloadType, TWriteScope_contra]):
    def create(
        self, scope: TWriteScope_contra
    ) -> IMessageHandler[TMessagePayloadType]: ...


class ScopedMessageHandlerProvider(
    IMessageHandler[TMessagePayloadType],
    Generic[TMessagePayloadType, TWriteScope],
):
    def __init__(
        self,
        write_scope_runner: IWriteScopeRunner[TWriteScope],
        factory: Callable[[TWriteScope], IMessageHandler[TMessagePayloadType]],
    ) -> None:
        self._write_scope_runner = write_scope_runner
        self._factory = factory
        self.handler_key = f"{self.__class__.__name__}:{id(self)}"

    def create(self, scope: TWriteScope) -> IMessageHandler[TMessagePayloadType]:
        return self._factory(scope)

    def handle_message(self, message: CloudMessage[TMessagePayloadType]) -> None:
        self._write_scope_runner.run_in_write_scope(
            lambda scope: self.create(scope).handle_message(message)
        )

    def get_use_case(self, message: TMessagePayloadType) -> IUseCase:
        raise NotImplementedError(
            "Scoped providers materialize handlers inside a scope"
        )


class ScopedQueryHandlerProvider(
    IQueryHandler[TManager, TQuery, TView],
    Generic[TManager, TQuery, TView, TReadScope],
):
    def __init__(
        self,
        read_scope_runner: IReadScopeRunner[TReadScope],
        factory: Callable[[TReadScope], IQueryHandler[TManager, TQuery, TView]],
    ) -> None:
        self._read_scope_runner = read_scope_runner
        self._factory = factory

    @property
    def repository(self) -> ISearchRepository[TManager, TQuery, TView]:
        raise RuntimeError("Scoped query providers do not expose a stable repository")

    def get(self, query: TQuery) -> QueryResults[TView]:
        return self._read_scope_runner.run_in_read_scope(
            lambda scope: self._factory(scope).get(query)
        )


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
        if (
            repository is not None
            and repository.connection_manager is not self.uow.connection_manager
        ):
            self.uow.attach_repo(repository)
        for repository in repositories:
            if repository.connection_manager is self.uow.connection_manager:
                continue
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
            self.event_bus.save_to_outbox(*messages)
        self.event_bus.publish_from_outbox()


class EventHandlerBase(MessageHandler[TEvent, TRepository]):
    class UseCaseImpl(IUseCase):
        def __init__(
            self,
            event_handler: "EventHandlerBase[TEvent, TRepository]",
            event: TEvent,
        ) -> None:
            self.event_handler = event_handler
            self.event = event

        def execute(self) -> Iterable[TEvento]:
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

        def execute(self) -> Iterable[TEvento]:
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
        items = list(results)
        return QueryResults[TView].new(items=items, limit=len(items))
