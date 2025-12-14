# pyright: reportMissingParameterType=none, reportGeneralTypeIssues=none

from typing import Any

from hexagonal.adapters.drivens.buses.base import BaseBusInfrastructure, QueryBus
from hexagonal.ports.drivens import (
    IInboxRepository,
    IOutboxRepository,
    TManager,
)

from .command_bus import InMemoryCommandBus, InMemoryQueueCommandBus
from .event_bus import InMemoryEventBus, InMemoryQueueEventBus


class InMemoryBusInfrastructure(BaseBusInfrastructure[TManager]):
    def __init__(
        self,
        inbox: IInboxRepository[TManager],
        outbox: IOutboxRepository[TManager],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(
            InMemoryCommandBus(inbox, outbox),
            InMemoryEventBus(inbox, outbox),
            QueryBus[TManager](),
            inbox,
            outbox,
            *args,
            **kwargs,
        )


class InMemoryQueueBusInfrastructure(BaseBusInfrastructure[TManager]):
    def __init__(
        self,
        inbox: IInboxRepository[TManager],
        outbox: IOutboxRepository[TManager],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(
            InMemoryQueueCommandBus(inbox, outbox),
            InMemoryQueueEventBus(inbox, outbox),
            QueryBus(),
            inbox,
            outbox,
        )
