from hexagonal.domain import CloudMessage, TCommand, TEvent
from hexagonal.ports.drivens import TManager
from hexagonal.ports.drivers import IBaseApplication, IBusApp


class ApplicationProxyAdapter(IBaseApplication[TManager]):
    def __init__(self, application: IBaseApplication[TManager]):
        self._application = application

    @property
    def bus_app(self):
        return self._application.bus_app

    @property
    def bus_infrastructure(self):
        return self._application.bus_infrastructure

    @property
    def command_bus(self):
        return self._application.command_bus

    @property
    def query_bus(self):
        return self._application.query_bus

    @property
    def event_bus(self):
        return self._application.event_bus

    def bootstrap(self, bus_app: IBusApp[TManager]) -> None:
        self._application.bootstrap(bus_app)

    def dispatch_and_wait_events(
        self,
        command: CloudMessage[TCommand],
        *event_types: type[TEvent],
    ) -> dict[type[TEvent], TEvent | None]:
        return self._application.dispatch_and_wait_events(command, *event_types)
