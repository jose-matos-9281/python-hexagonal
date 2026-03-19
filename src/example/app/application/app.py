# pyright: reportMissingParameterType=none, reportGeneralTypeIssues=none

from example.app.ports.drivens import IexampleInfrastructure
from example.app.ports.drivers import IexampleApp
from example.contacto.application import ContactoApp
from hexagonal.application import ComposableBusApp
from hexagonal.ports.drivens import TManager


class exampleBusApp(ComposableBusApp[TManager]):
    def __init__(self, infrastructure: IexampleInfrastructure[TManager]):
        infrastructure.verify()
        self._infra = infrastructure

    @property
    def uow(self):
        return self._infra.uow

    def bootstrap(self, command_bus, query_bus, event_bus) -> None:
        command_bus.configure_scope_runtime(
            write_scope_runner=self._infra.write_scope_runner,
            outbox_repository_getter=lambda scope: scope.outbox_repository,
        )
        event_bus.configure_scope_runtime(
            write_scope_runner=self._infra.write_scope_runner,
            outbox_repository_getter=lambda scope: scope.outbox_repository,
        )
        query_bus.configure_read_scope_runtime(self._infra.read_scope_runner)


class exampleApp(IexampleApp[TManager], ComposableBusApp[TManager]):
    def __init__(self, infrastructure: IexampleInfrastructure[TManager]):
        self._infrastructure = infrastructure
        contacto = ContactoApp(infrastructure.contacto, infrastructure)
        self._buses = exampleBusApp(infrastructure)
        super().__init__(contacto + self._buses)

    @property
    def infrastructure(self) -> IexampleInfrastructure[TManager]:
        return self._infrastructure
