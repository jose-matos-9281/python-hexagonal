from hexagonal.application import InfrastructureGroup
from hexagonal.ports.drivens import (
    IBaseInfrastructure,
    IBusInfrastructure,
    ICommandBus,
    IEventBus,
    IQueryBus,
    TManager,
)


class BaseBusInfrastructure(IBusInfrastructure[TManager], InfrastructureGroup):
    def __init__(
        self,
        command_bus: ICommandBus[TManager],
        event_bus: IEventBus[TManager],
        query_bus: IQueryBus[TManager],
        *args: IBaseInfrastructure,
    ):
        self._command_bus = command_bus
        self._event_bus = event_bus
        self._query_bus = query_bus
        super().__init__(self._command_bus, self._event_bus, self._query_bus, *args)

    @property
    def command_bus(self):
        self.verify()
        return self._command_bus

    @property
    def event_bus(self):
        self.verify()
        return self._event_bus

    @property
    def query_bus(self):
        self.verify()
        return self._query_bus
