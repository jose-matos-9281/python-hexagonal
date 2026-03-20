from example.contacto.ports.drivens import IAppContactoInfrastructure
from example.contacto.ports.drivers import IContactoApp
from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)


class ContactoAppProxyAdapter(IContactoApp[TManager]):
    def __init__(self, app: IContactoApp[TManager]) -> None:
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
    def infrastructure(self) -> IAppContactoInfrastructure[TManager]:
        return self.app.infrastructure


__all__ = ["ContactoAppProxyAdapter"]
