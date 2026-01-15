from abc import abstractmethod
from typing import Generic

from example.domain.example import ExampleAggregate, ExampleId
from hexagonal.ports.drivens import (
    IAggregateRepository,
    IBaseInfrastructure,
    IUnitOfWork,
    TManager,
)

IExampleRepository = IAggregateRepository[TManager, ExampleAggregate, ExampleId]


class IAppExampleInfrastructure(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def example_repository(self) -> IExampleRepository[TManager]: ...

    @property
    @abstractmethod
    def uow(self) -> IUnitOfWork[TManager]: ...
