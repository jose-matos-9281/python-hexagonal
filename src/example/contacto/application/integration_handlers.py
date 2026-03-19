from example.app.ports.drivens import IexampleInfrastructure
from hexagonal.application import ComposableBusApp, ScopedMessageHandlerProvider
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
        scope_provider: IexampleInfrastructure[TManager],
    ):
        self._uow = uow
        self.scope_provider = scope_provider

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
            ScopedMessageHandlerProvider(
                self.scope_provider.write_scope_runner,
                lambda scope: EntidadContactoCorrespondeHandler(
                    event_bus,
                    scope.uow,
                    scope.contacto_repository,
                ),
            ),
        )
