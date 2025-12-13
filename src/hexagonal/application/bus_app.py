import logging

from hexagonal.ports.drivens import (
    ICommandBus,
    IEventBus,
    IQueryBus,
    IUnitOfWork,
    TManager,
)
from hexagonal.ports.drivers import IBusApp

logger = logging.getLogger(__name__)


class ComposableBusApp(IBusApp[TManager]):
    def __init__(self, bus_app: IBusApp[TManager]):
        super().__init__()
        self._bus_app = bus_app

    def bootstrap(
        self,
        command_bus: ICommandBus[TManager],
        query_bus: IQueryBus[TManager],
        event_bus: IEventBus[TManager],
    ) -> None:
        self._bus_app.bootstrap(command_bus, query_bus, event_bus)

    @property
    def uow(self) -> IUnitOfWork[TManager]:
        return self._bus_app.uow

    def __or__(self, other: IBusApp[TManager]) -> "ComposableBusApp[TManager]":
        other_is_root = other.bus_apps if isinstance(other, BusAppGroup) else [other]

        self_is_root = self.bus_apps if isinstance(self, BusAppGroup) else [self]
        return BusAppGroup(self.uow, *self_is_root, *other_is_root)

    def __add__(self, other: IBusApp[TManager]) -> "ComposableBusApp[TManager]":
        return self.__or__(other)

    def __and__(self, other: IBusApp[TManager]) -> "ComposableBusApp[TManager]":
        return BusAppGroup(self.uow, self, other)


class BusAppGroup(ComposableBusApp[TManager]):
    def __init__(
        self,
        uow: IUnitOfWork[TManager],
        bus_app: IBusApp[TManager],
        *bus_apps: IBusApp[TManager],
    ):
        self._bus_apps = [bus_app, *bus_apps]
        self._uow = uow

    @property
    def uow(self) -> IUnitOfWork[TManager]:
        return self._uow

    @property
    def bus_apps(self) -> list[IBusApp[TManager]]:
        return self._bus_apps

    def bootstrap(
        self,
        command_bus: ICommandBus[TManager],
        query_bus: IQueryBus[TManager],
        event_bus: IEventBus[TManager],
    ) -> None:
        for bus_app in self._bus_apps:
            bus_app.bootstrap(command_bus, query_bus, event_bus)
