from example.app.ports.drivers import IexampleApp
from hexagonal.ports.drivens import TManager


class exampleAppProxyAdapter(IexampleApp[TManager]):
    def __init__(self, app: IexampleApp[TManager]):
        self.app = app

    @property
    def uow(self):
        return self.app.uow

    def bootstrap(self, command_bus, query_bus, event_bus):  # type: ignore
        return self.app.bootstrap(command_bus, query_bus, event_bus)

    @property
    def infrastructure(self):
        return self.app.infrastructure
