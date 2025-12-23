from abc import abstractmethod
from typing import Generic

from example.domain import ExampleAggregate, ExampleId
from hexagonal.ports.drivens import (
    IAggregateRepository,
    IBaseInfrastructure,
    IUnitOfWork,
    TManager,
)
from hexagonal.ports.drivers import IBusApp

IExampleRepository = IAggregateRepository[TManager, ExampleAggregate, ExampleId]


class IAppExampleInfrastructure(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def example_repository(self) -> IExampleRepository[TManager]: ...

    @property
    @abstractmethod
    def uow(self) -> IUnitOfWork[TManager]: ...


class IExampleApp(IBusApp[TManager]):
    @property
    @abstractmethod
    def infrastructure(self) -> IAppExampleInfrastructure[TManager]: ...
