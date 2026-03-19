import threading
from abc import ABC, abstractmethod
from asyncio import Event
from typing import Any, Callable, Generic, Literal, Type, overload

from hexagonal.domain import (
    CloudMessage,
    Query,
    QueryOne,
    QueryResult,
    QueryResults,
    TCommand,
    TEvent,
    TQuery,
    TView,
)

from .application import IMessageHandler, IQueryHandler
from .infrastructure import IBaseInfrastructure
from .repository import IInboxRepository, IOutboxRepository, TManager


class IBaseMessageBus(IBaseInfrastructure, ABC, Generic[TManager]):
    @property
    @abstractmethod
    def inbox_repository(self) -> IInboxRepository[TManager]: ...

    @property
    @abstractmethod
    def outbox_repository(self) -> IOutboxRepository[TManager]: ...

    @abstractmethod
    def publish_from_outbox(self, limit: int | None = None):
        """Publicar mensajes desde la outbox., hasta el límite especificado."""
        ...

    @abstractmethod
    def save_to_outbox(self, *messages: CloudMessage[Any]) -> None:
        """Guardar mensajes en la outbox usando el scope activo si existe."""
        ...

    @abstractmethod
    def configure_scope_runtime(
        self,
        *,
        write_scope_runner: Any | None = None,
        outbox_repository_getter: Callable[[Any], IOutboxRepository[TManager]]
        | None = None,
    ) -> None:
        """Configurar acceso a repositorios scope-aware para outbox."""
        ...

    @abstractmethod
    def consume(self, limit: int | None = None):
        """Consumir mensajes desde la inbox, hasta el límite especificado."""
        ...

    async def consume_async(self, shutdown_event: Event | threading.Event): ...


class ICommandBus(IBaseMessageBus[TManager], ABC):
    @abstractmethod
    def register_handler(
        self, command_type: Type[TCommand], handler: IMessageHandler[TCommand]
    ) -> None:
        """Registrar un manejador para un tipo de comando."""
        ...

    @abstractmethod
    def unregister_handler(self, command_type: Type[TCommand]) -> None:
        """Desregistrar el manejador para un tipo de comando."""
        ...

    @abstractmethod
    def dispatch(
        self,
        command: TCommand | CloudMessage[TCommand],
        *,
        to_outbox: bool = False,
    ) -> None:
        """Despachar un comando para su procesamiento."""
        ...

    @abstractmethod
    def process_command(self, command: CloudMessage[TCommand]) -> None:
        """Procesar un comando recibido."""
        ...


class IEventBus(IBaseMessageBus[TManager], ABC):
    @abstractmethod
    def subscribe(self, event_type: Type[TEvent], handler: IMessageHandler[TEvent]):
        """Suscribir un manejador a un tipo de evento."""
        ...

    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type[TEvent],
        *handlers: IMessageHandler[TEvent],
    ): ...

    @abstractmethod
    def publish(self, *events: CloudMessage[TEvent]) -> None:
        """Publicar un evento a todos sus suscriptores."""
        ...

    @abstractmethod
    def process_events(self, *events: CloudMessage[TEvent]) -> None: ...

    #  wait for
    @overload
    def wait_for_publish(
        self, event_type: Type[TEvent], handler: Callable[[TEvent], None]
    ) -> None: ...
    @overload
    def wait_for_publish(
        self, event_type: Type[TEvent]
    ) -> Callable[[Callable[[TEvent], None]], None]: ...

    @abstractmethod
    def wait_for_publish(
        self, event_type: Type[TEvent], handler: Callable[[TEvent], None] | None = None
    ) -> Callable[[Callable[[TEvent], None]], None] | None: ...


class IQueryBus(IBaseInfrastructure, Generic[TManager]):
    @abstractmethod
    def configure_read_scope_runtime(
        self, read_scope_runner: Any | None = None
    ) -> None: ...

    @abstractmethod
    def register_handler(
        self,
        query_type: Type[TQuery],
        handler: IQueryHandler[TManager, TQuery, TView],
    ): ...

    @abstractmethod
    def unregister_handler(self, query_type: Type[Query[TView]]): ...

    @overload
    def get(
        self,
        query: QueryOne[TView],
        *,
        one: bool = False,
    ) -> QueryResult[TView]: ...

    @overload
    def get(self, query: Query[TView], *, one: Literal[True]) -> QueryResult[TView]: ...

    @overload
    def get(
        self,
        query: Query[TView],
        *,
        one: Literal[False] = False,
    ) -> QueryResults[TView]: ...

    @abstractmethod
    def get(
        self,
        query: Query[TView] | QueryOne[TView],
        *,
        one: bool = False,
    ) -> QueryResult[TView] | QueryResults[TView]: ...


class IBusInfrastructure(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def command_bus(self) -> ICommandBus[TManager]: ...

    @property
    @abstractmethod
    def event_bus(self) -> IEventBus[TManager]: ...

    @property
    @abstractmethod
    def query_bus(self) -> IQueryBus[TManager]: ...
