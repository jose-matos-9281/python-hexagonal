from example.app.ports.drivers import IexampleApp
from example.app.ports.drivens import IexampleInfrastructure
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)


class exampleAppProxyAdapter(IexampleApp[TManager]):
    def __init__(self, app: IexampleApp[TManager]) -> None:
        self.app = app

    @property
    def uow(self) -> IUnitOfWork[TManager]:
        return self.app.uow

    def bootstrap(
        self,
        command_bus: ICommandBus[TManager],
        query_bus: IQueryBus[TManager],
        event_bus: IEventBus[TManager],
    ) -> None:
        self.app.bootstrap(command_bus, query_bus, event_bus)

    @property
    def infrastructure(self) -> IexampleInfrastructure[TManager]:
        return self.app.infrastructure


__all__ = ["exampleAppProxyAdapter"]
