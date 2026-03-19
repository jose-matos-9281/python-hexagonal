from example.contacto.domain.contacto import GetContactoById
from example.contacto.ports.drivens import IContactoRepository
from hexagonal.application import ComposableBusApp, GetAggregateByIdHandler
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)

from .use_cases import (
    CrearContacto,
    CrearContactoHandler,
    ValidarContacto,
    ValidarContactoHandler,
)


class ContactoBusApp(ComposableBusApp[TManager]):
    def __init__(
        self,
        uow: IUnitOfWork[TManager],
        repository: IContactoRepository[TManager],
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
            CrearContacto,
            CrearContactoHandler(event_bus, self.uow, self.repository),
        )
        command_bus.register_handler(
            ValidarContacto,
            ValidarContactoHandler(event_bus, self.uow, self.repository),
        )
        query_bus.register_handler(
            GetContactoById, GetAggregateByIdHandler(self.repository)
        )
