from example.app.ports.drivens import IexampleInfrastructure
from example.contacto.domain.entidad import GetEntidadById
from hexagonal.application import (
    ComposableBusApp,
    GetEntityByIdHandler,
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
    BorrarEntidad,
    BorrarEntidadHandler,
    CrearEntidad,
    CrearEntidadHandler,
)


class EntidadBusApp(ComposableBusApp[TManager]):
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
            CrearEntidad,
            ScopedMessageHandlerProvider(
                self.scope_provider.write_scope_runner,
                lambda scope: CrearEntidadHandler(
                    event_bus,
                    scope.uow,
                    scope.entidad_repository,
                ),
            ),
        )
        command_bus.register_handler(
            BorrarEntidad,
            ScopedMessageHandlerProvider(
                self.scope_provider.write_scope_runner,
                lambda scope: BorrarEntidadHandler(
                    event_bus,
                    scope.uow,
                    scope.entidad_repository,
                ),
            ),
        )

        query_bus.register_handler(
            GetEntidadById,
            ScopedQueryHandlerProvider(
                self.scope_provider.read_scope_runner,
                lambda manager: GetEntityByIdHandler(
                    self.scope_provider.build_entidad_repository(manager)
                ),
            ),
        )
