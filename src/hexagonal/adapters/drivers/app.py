from hexagonal.domain import CloudMessage, CommandOutcome, TCommand, TEvento
from hexagonal.ports.drivens import (
    IBusInfrastructure,
    ICommandBus,
    IEventBus,
    IQueryBus,
    TManager,
)
from hexagonal.ports.drivers import IBaseApplication, IBusApp


class ApplicationProxyAdapter(IBaseApplication[TManager]):
    def __init__(self, application: IBaseApplication[TManager]) -> None:
        self._application = application

    @property
    def bus_app(self) -> IBusApp[TManager]:
        return self._application.bus_app

    @property
    def bus_infrastructure(self) -> IBusInfrastructure[TManager]:
        return self._application.bus_infrastructure

    @property
    def command_bus(self) -> ICommandBus[TManager]:
        return self._application.command_bus

    @property
    def query_bus(self) -> IQueryBus[TManager]:
        return self._application.query_bus

    @property
    def event_bus(self) -> IEventBus[TManager]:
        return self._application.event_bus

    def bootstrap(self, bus_app: IBusApp[TManager]) -> None:
        self._application.bootstrap(bus_app)

    def dispatch_and_wait_events(
        self,
        command: CloudMessage[TCommand],
        *event_types: type[TEvento],
    ) -> CommandOutcome[TCommand]:
        return self._application.dispatch_and_wait_events(command, *event_types)


__all__ = ["ApplicationProxyAdapter"]
