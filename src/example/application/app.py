from example.ports.drivens import IAppExampleInfrastructure
from example.ports.drivers import IExampleApp
from hexagonal.application.bus_app import BusAppGroup
from hexagonal.ports.drivens import (
    TManager,
)

from .example import ExampleBusApp


class ExampleApp(IExampleApp[TManager], BusAppGroup[TManager]):
    def __init__(self, infrastructure: IAppExampleInfrastructure[TManager]):
        infrastructure.verify()
        self._infra = infrastructure
        self._example_bus_app = ExampleBusApp(
            uow=self._infra.uow,
            repository=self._infra.example_repository,
        )
        super().__init__(infrastructure.uow, self._example_bus_app)

    @property
    def infrastructure(self) -> IAppExampleInfrastructure[TManager]:
        return self._infra
