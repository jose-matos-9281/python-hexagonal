from abc import ABC, abstractmethod
from typing import Generic

from hexagonal.domain import CloudMessage, TCommand, TEvent
from hexagonal.ports.drivens import (
    IBusInfrastructure,
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)


class IBusApp(ABC, Generic[TManager]):
    @property
    @abstractmethod
    def uow(self) -> IUnitOfWork[TManager]: ...

    @abstractmethod
    def bootstrap(
        self,
        command_bus: ICommandBus[TManager],
        query_bus: IQueryBus[TManager],
        event_bus: IEventBus[TManager],
    ) -> None: ...


class IBaseApplication(ABC, Generic[TManager]):
    @property
    @abstractmethod
    def bus_app(self) -> IBusApp[TManager]: ...

    @property
    @abstractmethod
    def bus_infrastructure(self) -> IBusInfrastructure[TManager]: ...

    @property
    @abstractmethod
    def command_bus(self) -> ICommandBus[TManager]: ...

    @property
    @abstractmethod
    def query_bus(self) -> IQueryBus[TManager]: ...

    @property
    @abstractmethod
    def event_bus(self) -> IEventBus[TManager]: ...

    @abstractmethod
    def bootstrap(self, bus_app: IBusApp[TManager]) -> None: ...

    @abstractmethod
    def dispatch_and_wait_events(
        self,
        command: CloudMessage[TCommand],
        *event_types: type[TEvent],
    ) -> dict[type[TEvent], TEvent | None]: ...
