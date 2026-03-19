from example.contacto.ports.drivens import IContactoRepository
from hexagonal.application import ComposableBusApp
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    IUseCase,
    TManager,
)

from .contacto.use_cases import ContactoEventHandler, MarcarContactadoUseCase
from .entidad_contacto import EntidadContactoCorresponde


class EntidadContactoCorrespondeHandler(
    ContactoEventHandler[EntidadContactoCorresponde]
):
    def get_use_case(self, message: EntidadContactoCorresponde) -> IUseCase:
        return MarcarContactadoUseCase(
            self.repository,
            message.contacto,
            message.usuario,
        )


class IntegrationContactoBusApp(ComposableBusApp[TManager]):
    def __init__(
        self,
        uow: IUnitOfWork[TManager],
        repository: IContactoRepository[TManager],
    ):
        self._uow = uow
        self.repository: IContactoRepository[TManager] = repository

    @property
    def uow(self) -> IUnitOfWork[TManager]:
        return self._uow

    def bootstrap(
        self,
        command_bus: ICommandBus[TManager],
        query_bus: IQueryBus[TManager],
        event_bus: IEventBus[TManager],
    ) -> None:
        event_bus.subscribe(
            EntidadContactoCorresponde,
            EntidadContactoCorrespondeHandler(
                event_bus,
                self.uow,
                self.repository,
            ),
        )
