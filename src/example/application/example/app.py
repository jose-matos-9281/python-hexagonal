from example.ports.drivens import IExampleRepository
from hexagonal.application import (
    ComposableBusApp,
    GetByIdHandler,
)
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)

from .use_cases import (
    CambiarNombreExample,
    CambiarNombreExampleHandler,
    CrearExampleHandler,
    CreateExample,
    DeleteExample,
    DeleteExampleHandler,
    GetExampleById,
)


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
