import logging

from hexagonal.entrypoints.bus import (
    BusEntrypointGroup,
    InMemoryBusEntrypoint,
    InMemoryQueueBusEntrypoint,
)
from hexagonal.ports.drivens import TManager

logger = logging.getLogger(__name__)


# class ServiceBus(BusEntrypoint[TManager]):
#     name = "service_bus"

#     @classmethod
#     def get(cls, env: Optional[Mapping[str, str]] = None):
#         from .service_bus import ServiceBusBusEntrypoint

#         ServiceBusBusEntrypoint[TManager].setOutbox(cls.OUTBOX)
#         return ServiceBusBusEntrypoint[TManager].get(env)


class BusEntrypointGroupApp(BusEntrypointGroup[TManager]):
    env_key = "ENV_BUS"
    entrypoints = [
        InMemoryBusEntrypoint[TManager],
        InMemoryQueueBusEntrypoint[TManager],
        # ServiceBus[TManager],
    ]
    env = {"ENV_BUS": "inmemory_queue"}
