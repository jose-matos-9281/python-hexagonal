from example.contacto.domain.entidad import GetEntidadById
from example.contacto.ports.drivens import IEntidadRepository
from hexagonal.application import ComposableBusApp, GetEntityByIdHandler
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)

from .use_cases import (
    BorrarEntidad,
    BorrarEntidadHandler,
    CrearEntidad,
    CrearEntidadHandler,
)


class EntidadBusApp(ComposableBusApp[TManager]):
    def __init__(
        self,
        uow: IUnitOfWork[TManager],
        repository: IEntidadRepository[TManager],
    ):
        self._uow = uow
        self.repository = repository

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
            CrearEntidad,
            CrearEntidadHandler(event_bus, self.uow, self.repository),
        )
        command_bus.register_handler(
            BorrarEntidad,
            BorrarEntidadHandler(event_bus, self.uow, self.repository),
        )

        query_bus.register_handler(
            GetEntidadById,
            GetEntityByIdHandler(self.repository),
        )
