from example.app.ports.drivens import IexampleInfrastructure
from example.contacto.domain.contacto import GetContactoById
from hexagonal.application import (
    ComposableBusApp,
    GetAggregateByIdHandler,
    ScopedMessageHandlerProvider,
    ScopedQueryHandlerProvider,
)
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
        command_bus.register_handler(
            CrearContacto,
            ScopedMessageHandlerProvider(
                self.scope_provider.write_scope_runner,
                lambda scope: CrearContactoHandler(
                    event_bus,
                    scope.uow,
                    scope.contacto_repository,
                ),
            ),
        )
        command_bus.register_handler(
            ValidarContacto,
            ScopedMessageHandlerProvider(
                self.scope_provider.write_scope_runner,
                lambda scope: ValidarContactoHandler(
                    event_bus,
                    scope.uow,
                    scope.contacto_repository,
                ),
            ),
        )
        query_bus.register_handler(
            GetContactoById,
            ScopedQueryHandlerProvider(
                self.scope_provider.read_scope_runner,
                lambda manager: GetAggregateByIdHandler(
                    self.scope_provider.build_contacto_repository(manager)
                ),
            ),
        )
