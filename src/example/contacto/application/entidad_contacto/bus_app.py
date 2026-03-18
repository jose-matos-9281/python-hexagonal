from example.contacto.ports.drivens import IEntidadContactoRepository
from hexagonal.application import ComposableBusApp, GetAggregateByIdHandler
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)

from .use_cases import (
    CrearEntidadContacto,
    CrearEntidadContactoHandler,
    GetEntidadContactoById,
    ValidarEntidadContacto,
    ValidarEntidadContactoHandler,
)


class EntidadContactoBusApp(ComposableBusApp[TManager]):
    def __init__(
        self,
        uow: IUnitOfWork[TManager],
        repository: IEntidadContactoRepository[TManager],
    ):
        self._uow = uow
        self.repository: IEntidadContactoRepository[TManager] = repository

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
            CrearEntidadContacto,
            CrearEntidadContactoHandler(event_bus, self.uow, self.repository),
        )
        command_bus.register_handler(
            ValidarEntidadContacto,
            ValidarEntidadContactoHandler(event_bus, self.uow, self.repository),
        )
        query_bus.register_handler(
            GetEntidadContactoById,
            GetAggregateByIdHandler(self.repository),
        )
