import logging
from abc import ABC
from typing import Mapping, Optional, Type, cast

from hexagonal.adapters.drivens.buses.inmemory import (
    InMemoryBusInfrastructure,
    InMemoryQueueBusInfrastructure,
)
from hexagonal.entrypoints.base import Entrypoint, EntrypointGroup
from hexagonal.ports.drivens import (
    IBusInfrastructure,
    IPairInboxOutbox,
    TManager,
)

logger = logging.getLogger(__name__)


class BusEntrypoint(Entrypoint[IBusInfrastructure[TManager]], ABC):
    env = {"ONLY_INTEGRATION": "False"}
    OUTBOX: Type[Entrypoint[IPairInboxOutbox[TManager]]]

    @classmethod
    def setOutbox(cls, outbox: Type[Entrypoint[IPairInboxOutbox[TManager]]]):
        cls.OUTBOX = outbox


class InMemoryBusEntrypoint(BusEntrypoint[TManager]):
    name = "inmemory"

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        env = cls.construct_env(env)
        outbox = cls.OUTBOX.get(env)
        logger.info("Using %s for events", type(outbox).__name__)
        buses = InMemoryBusInfrastructure(outbox.inbox, outbox.outbox)
        buses.initialize(env)
        return buses


class InMemoryQueueBusEntrypoint(BusEntrypoint[TManager]):
    name = "inmemory_queue"

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        env = cls.construct_env(env)
        outbox = cls.OUTBOX.get(env)
        logger.info("Using %s for events", type(outbox).__name__)
        buses = InMemoryQueueBusInfrastructure(outbox.inbox, outbox.outbox)
        buses.initialize(env)
        return buses


class BusEntrypointGroup(EntrypointGroup[IBusInfrastructure[TManager]]):
    env_key = "ENV_BUS"
    entrypoints = [
        InMemoryBusEntrypoint[TManager],
        InMemoryQueueBusEntrypoint[TManager],
    ]
    env = {"ENV_BUS": "inmemory_queue"}

    @classmethod
    def getEntrypoint(
        cls, env: Optional[Mapping[str, str]] = None
    ) -> Type[BusEntrypoint[TManager]]:
        entry = super().getEntrypoint(env)

        return cast(Type[BusEntrypoint[TManager]], entry)
