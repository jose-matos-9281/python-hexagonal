from datetime import datetime
from typing import Any, Self, TypeVar

from example.domain.example import ExampleId, ExampleState
from example.ports.drivens import IExampleRepository
from hexagonal.application import CommandHandler
from hexagonal.domain import Command, DomainEvent, IntegrationEvent
from hexagonal.ports.drivens import IEventBus, IUnitOfWork, TManager


# Define example name space commands and events
class ExampleCommand(Command, topic_suffix="Example"): ...


class ExampleDomainEvent(DomainEvent, topic_suffix="Example"):
    id_example: ExampleId


class ExampleIntegrationEvent(IntegrationEvent, topic_suffix="Example"):
    id_example: ExampleId


class ExampleSnapshot(ExampleIntegrationEvent, topic_suffix="Snapshot"):
    nombre: str
    created_on: datetime
    updated_on: datetime

    @classmethod
    def new(cls, state: ExampleState) -> Self:
        return cls(
            id_example=state.id,
            nombre=state.name,
            created_on=state.created_on,
            updated_on=state.modified_on,
        )


T = TypeVar("T", bound=ExampleCommand)


class ExampleCommandHandler(CommandHandler[T]):
    repository: IExampleRepository[Any]

    def __init__(
        self,
        event_bus: IEventBus[TManager],
        uow: IUnitOfWork[TManager],
        repository: IExampleRepository[TManager],
    ) -> None:
        super().__init__(event_bus, uow, repository)
        self.repository = repository
