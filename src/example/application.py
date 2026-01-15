from datetime import datetime
from typing import Any, List, Optional, Self, Type, TypeVar
from uuid import UUID

from example.domain import ExampleAggregate, ExampleId, ExampleState
from example.ports import IAppExampleInfrastructure, IExampleApp, IExampleRepository
from hexagonal.application import (
    CommandHandler,
    ComposableBusApp,
    GetById,
    GetByIdHandler,
)
from hexagonal.application.api import BaseAPI, TBaseApp
from hexagonal.application.bus_app import BusAppGroup
from hexagonal.domain import Command, DomainEvent, IntegrationEvent
from hexagonal.domain.base import TEvento
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)


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


# Use Case Create Example
class CreateExample(ExampleCommand, topic_suffix="Create"):
    nombre: str

    @classmethod
    def new(cls, nombre: str):
        return cls(nombre=nombre)


class ExampleCreated(ExampleDomainEvent, topic_suffix="Created"):
    nombre: str

    @classmethod
    def from_state(cls, state: ExampleState) -> Self:
        return cls(id_example=state.id, nombre=state.name)

    @classmethod
    def new(cls, id_example: ExampleId, nombre: str) -> Self:
        return cls(id_example=id_example, nombre=nombre)


class CrearExampleHandler(ExampleCommandHandler[CreateExample]):
    def execute(self, command: CreateExample):
        print(
            f"    [DEBUG CrearExampleHandler] Creating aggregate with nombre={command.nombre}"
        )
        example_agg = ExampleAggregate(nombre=command.nombre)
        print(f"    [DEBUG CrearExampleHandler] Aggregate id={example_agg.id}")
        self.repository.save(example_agg)
        events: list[ExampleDomainEvent | ExampleIntegrationEvent] = [
            ExampleCreated.from_state(example_agg.state),
            ExampleSnapshot.new(example_agg.state),
        ]
        print(
            f"    [DEBUG CrearExampleHandler] Events created, id_example={events[0].id_example}"
        )
        return events


# Use Case Change Name Example
class CambiarNombreExample(ExampleCommand, topic_suffix="CambiarNombre"):
    id_example: ExampleId
    nuevo_nombre: str

    @classmethod
    def new(cls, id: UUID, nuevo_nombre: str) -> Self:
        return cls(id_example=ExampleId(value=id), nuevo_nombre=nuevo_nombre)


class NombreCambiadoExample(ExampleDomainEvent, topic_suffix="NombreCambiado"):
    nuevo_nombre: str

    @classmethod
    def from_state(cls, state: ExampleState) -> Self:
        return cls(id_example=state.id, nuevo_nombre=state.name)

    @classmethod
    def new(cls, id_example: ExampleId, nuevo_nombre: str) -> Self:
        return cls(id_example=id_example, nuevo_nombre=nuevo_nombre)


class CambiarNombreExampleHandler(ExampleCommandHandler[CambiarNombreExample]):
    def execute(self, command: CambiarNombreExample):
        example_agg = self.repository.get(command.id_example)
        example_agg.change_name(command.nuevo_nombre)
        self.repository.save(example_agg)
        events: list[ExampleDomainEvent | ExampleIntegrationEvent] = [
            NombreCambiadoExample.from_state(example_agg.state),
            ExampleSnapshot.new(example_agg.state),
        ]
        return events


# Use Case Delete Example
class DeleteExample(ExampleCommand, topic_suffix="Eliminar"):
    id_example: ExampleId

    @classmethod
    def new(cls, id: UUID) -> Self:
        return cls(id_example=ExampleId(value=id))


class ExampleDeleted(ExampleDomainEvent, topic_suffix="Deleted"):
    @classmethod
    def from_state(cls, state: ExampleState) -> Self:
        return cls(id_example=state.id)

    @classmethod
    def new(cls, id_example: ExampleId) -> Self:
        return cls(id_example=id_example)


class DeleteExampleHandler(ExampleCommandHandler[DeleteExample]):
    def execute(self, command: DeleteExample):
        example_agg = self.repository.delete(command.id_example)
        events: list[ExampleDomainEvent] = [
            ExampleDeleted.from_state(example_agg.state),
        ]
        return events


# Query to get Example by Id
class GetExampleById(GetById[ExampleAggregate, ExampleId]):
    @classmethod
    def new(cls, id: ExampleId | UUID, *_: Any, **__: Any):
        if isinstance(id, UUID):
            id = ExampleId(value=id)
        return super().new(id=id, agg_type=ExampleAggregate)


# Register Handler in Bus App


class ExampleBusApp(ComposableBusApp[TManager]):
    def __init__(
        self,
        uow: IUnitOfWork[TManager],
        repository: IExampleRepository[TManager],
    ):
        self._uow = uow
        self.repository: IExampleRepository[TManager] = repository

    @property
    def uow(self) -> IUnitOfWork[TManager]:
        return self._uow

    def bootstrap(
        self,
        command_bus: ICommandBus[TManager],
        query_bus: IQueryBus[TManager],
        event_bus: IEventBus[TManager],
    ) -> None:
        command_bus.register_handler(
            CreateExample,
            CrearExampleHandler(
                event_bus=event_bus,
                uow=self.uow,
                repository=self.repository,
            ),
        )
        command_bus.register_handler(
            CambiarNombreExample,
            CambiarNombreExampleHandler(
                event_bus=event_bus,
                uow=self.uow,
                repository=self.repository,
            ),
        )
        command_bus.register_handler(
            DeleteExample,
            DeleteExampleHandler(
                event_bus=event_bus, uow=self.uow, repository=self.repository
            ),
        )

        query_bus.register_handler(GetExampleById, GetByIdHandler(self.repository))


class ExampleApp(IExampleApp[TManager], BusAppGroup[TManager]):
    def __init__(self, infrastructure: IAppExampleInfrastructure[TManager]):
        infrastructure.verify()
        self._infra = infrastructure
        self._example_bus_app = ExampleBusApp(
            uow=self._infra.uow,
            repository=self._infra.example_repository,
        )
        super().__init__(infrastructure.uow, self._example_bus_app)

    @property
    def infrastructure(self) -> IAppExampleInfrastructure[TManager]:
        return self._infra


class ExampleAPI(BaseAPI[TBaseApp]):
    def crear(
        self,
        nombre: str,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = CreateExample.new(nombre=nombre)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[ExampleSnapshot],
            async_dispatch=async_dispatch,
            **kwargs,
        )

    def cambiar_nombre(
        self,
        id: UUID,
        nuevo_nombre: str,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = CambiarNombreExample.new(id=id, nuevo_nombre=nuevo_nombre)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[ExampleSnapshot],
            async_dispatch=async_dispatch,
            **kwargs,
        )

    def eliminar(
        self,
        id: UUID,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = DeleteExample.new(id=id)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[ExampleDeleted],
            async_dispatch=async_dispatch,
            **kwargs,
        )

    def get(
        self,
        id: UUID,
        **kwargs: Any,
    ):
        return self._get_aggregate(id, GetExampleById)
