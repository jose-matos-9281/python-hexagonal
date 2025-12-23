# pyright: reportMissingParameterType=none, reportGeneralTypeIssues=none

from typing import Type

from hexagonal.adapters.drivers import ApplicationProxyAdapter
from hexagonal.application import Application
from hexagonal.ports.drivens import IPairInboxOutbox, TManager
from hexagonal.ports.drivers import IBaseApplication, IBusApp

from .base import Entrypoint
from .bus import BusEntrypoint, BusEntrypointGroup


class AppEntrypoint(Entrypoint[IBaseApplication[TManager]]):
    name = "AppEntrypoint"
    BUS_APP: Type[Entrypoint[IBusApp[TManager]]]
    OUTBOX: Type[Entrypoint[IPairInboxOutbox[TManager]]]
    BUS_INFRASTRUCTURE: Type[BusEntrypoint[TManager]]
    BUS_GROUP: Type[BusEntrypointGroup[TManager]] = BusEntrypointGroup[TManager]

    @classmethod
    def setBusApp(cls, bus_app: Type[Entrypoint[IBusApp[TManager]]]):
        cls.BUS_APP = bus_app

    @classmethod
    def setOutbox(cls, outbox: Type[Entrypoint[IPairInboxOutbox[TManager]]]):
        cls.OUTBOX = outbox

    @classmethod
    def setBusInfrastructure(cls, bus_infrastructure: Type[BusEntrypoint[TManager]]):
        cls.BUS_INFRASTRUCTURE = bus_infrastructure

    @classmethod
    def setBusEntrypointGroup(cls, bus_group: Type[BusEntrypointGroup[TManager]]):
        cls.BUS_GROUP = bus_group

    @classmethod
    def get(cls, env=None) -> IBaseApplication[TManager]:
        env = cls.construct_env(env)
        if not hasattr(cls, "BUS_APP"):
            raise ValueError("Bus app is not configured")
        if not hasattr(cls, "OUTBOX"):
            raise ValueError("Outbox is not configured")
        if not hasattr(cls, "BUS_INFRASTRUCTURE"):
            cls.setBusInfrastructure(cls.BUS_GROUP.getEntrypoint(env))

        cls.BUS_INFRASTRUCTURE.setOutbox(cls.OUTBOX)
        GeneralBusEntrypoint = cls.BUS_INFRASTRUCTURE

        bus_app = cls.BUS_APP.get(env)
        bus_infrastructure = GeneralBusEntrypoint.get(env)
        app = Application(bus_app, bus_infrastructure)
        return ApplicationProxyAdapter(app)
