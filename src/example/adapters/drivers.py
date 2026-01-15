from example.ports.drivers import IExampleApp
from hexagonal.ports.drivens import TManager


class ExampleAppProxyAdapter(IExampleApp[TManager]):
    def __init__(self, app: IExampleApp[TManager]):
        self.app = app

    @property
    def uow(self):
        return self.app.uow

    def bootstrap(self, command_bus, query_bus, event_bus):  # type: ignore
        return self.app.bootstrap(command_bus, query_bus, event_bus)

    @property
    def infrastructure(self):
        return self.app.infrastructure
