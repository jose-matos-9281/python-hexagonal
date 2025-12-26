from typing import ClassVar, Dict
from uuid import UUID

from eventsourcing.persistence import Mapper

from example.domain import ExampleAggregate, ExampleId
from example.ports import IAppExampleInfrastructure, IExampleApp, IExampleRepository
from hexagonal.adapters.drivens.repository.sqlite import (
    SQLiteConnectionContextManager,
    SQLiteRepositoryAdapter,
    SQLiteUnitOfWork,
)
from hexagonal.application import InfrastructureGroup
from hexagonal.ports.drivens import TManager


class SQLiteExampleRepositoryAdapter(
    SQLiteRepositoryAdapter[ExampleAggregate, ExampleId],
    IExampleRepository[SQLiteConnectionContextManager],
):
    ENV: ClassVar[Dict[str, str]] = {"TABLE_NAME": "Example"}


class SQLiteAppExampleInfrastructure(
    IAppExampleInfrastructure[SQLiteConnectionContextManager], InfrastructureGroup
):
    def __init__(
        self,
        manager: SQLiteConnectionContextManager,
        mapper: Mapper[UUID],
        uow: SQLiteUnitOfWork | None = None,
    ):
        self._example_repository = SQLiteExampleRepositoryAdapter(
            mapper,
            manager,
        )
        self._uow = uow or SQLiteUnitOfWork(self._example_repository)  # type: ignore
        if uow is None:
            return super().__init__(self._uow)

        return super().__init__(self._example_repository)

    @property
    def example_repository(self):
        return self._example_repository

    @property
    def uow(self):
        return self._uow


class ExampleAppProxyAdapter(IExampleApp[TManager]):
    def __init__(self, app: IExampleApp[TManager]):
        self.app = app

    @property
    def uow(self):
        return self.app.uow

    def bootstrap(self, command_bus, query_bus, event_bus):  # type: ignore
        return self.app.bootstrap(command_bus, query_bus, event_bus)

    @property
    def infrastructure(self):
        return self.app.infrastructure
