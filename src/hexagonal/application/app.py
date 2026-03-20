from typing import Generic, Type

from hexagonal.domain import CloudMessage, CommandOutcome, TCommand, TEvent
from hexagonal.domain.base import TEvento
from hexagonal.ports.drivens import (
    IBusInfrastructure,
    ICommandBus,
    IEventBus,
    IQueryBus,
    TManager,
)
from hexagonal.ports.drivers import IBaseApplication, IBusApp


class GetEvent(Generic[TEvent]):
    event: TEvent | None = None

    def __init__(self) -> None:
        self.event = None

    def __call__(self, event: TEvent) -> None:
        self.event = event


class Application(IBaseApplication[TManager]):
    def __init__(
        self,
        bus_app: IBusApp[TManager],
        bus_infrastructure: IBusInfrastructure[TManager],
    ) -> None:
        bus_infrastructure.verify()
        self._bus_infrastructure = bus_infrastructure
        self._bus_app = bus_app
        self.bootstrap(self._bus_app)

    @property
    def bus_app(self) -> IBusApp[TManager]:
        return self._bus_app

    @property
    def bus_infrastructure(self) -> IBusInfrastructure[TManager]:
        return self._bus_infrastructure

    @property
    def command_bus(self) -> ICommandBus[TManager]:
        return self._bus_infrastructure.command_bus

    @property
    def query_bus(self) -> IQueryBus[TManager]:
        return self._bus_infrastructure.query_bus

    @property
    def event_bus(self) -> IEventBus[TManager]:
        return self._bus_infrastructure.event_bus

    def bootstrap(self, bus_app: IBusApp[TManager]) -> None:
        bus_app.bootstrap(
            command_bus=self.command_bus,
            query_bus=self.query_bus,
            event_bus=self.event_bus,
        )

    def dispatch_and_wait_events(
        self,
        command: CloudMessage[TCommand],
        *event_types: Type[TEvento],
    ) -> CommandOutcome[TCommand]:
        handlers: dict[Type[TEvento], GetEvent[TEvento]] = {}
        for event_type in event_types:
            handler = GetEvent[TEvento]()
            handlers[event_type] = handler
            self.event_bus.wait_for_publish(event_type, handler)
        self.command_bus.dispatch(command)
        return CommandOutcome(
            command=command,
            events={
                event_type: handler.event for event_type, handler in handlers.items()
            },
        )
