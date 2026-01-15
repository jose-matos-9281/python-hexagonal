from typing import ClassVar, Dict
from uuid import UUID

from eventsourcing.persistence import Mapper

from example.domain import ExampleAggregate, ExampleId
from example.ports import IAppExampleInfrastructure, IExampleRepository
from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyRepositoryAdapter,
    SQLAlchemyUnitOfWork,
)
from hexagonal.application import InfrastructureGroup


class SQLAlchemyExampleRepositoryAdapter(
    SQLAlchemyRepositoryAdapter[ExampleAggregate, ExampleId],
    IExampleRepository[SQLAlchemyConnectionContextManager],
):
    """SQLAlchemy-based repository adapter for ExampleAggregate."""

    ENV: ClassVar[Dict[str, str]] = {"TABLE_NAME": "Example"}


class SQLAlchemyAppExampleInfrastructure(
    IAppExampleInfrastructure[SQLAlchemyConnectionContextManager], InfrastructureGroup
):
    """SQLAlchemy-based infrastructure for the Example application."""

    def __init__(
        self,
        manager: SQLAlchemyConnectionContextManager,
        mapper: Mapper[UUID],
        uow: SQLAlchemyUnitOfWork | None = None,
    ):
        self._example_repository = SQLAlchemyExampleRepositoryAdapter(
            mapper,
            manager,
        )
        self._uow = uow or SQLAlchemyUnitOfWork(
            self._example_repository, connection_manager=manager
        )
        if uow is None:
            return super().__init__(self._uow)

        return super().__init__(self._example_repository)

    @property
    def example_repository(self):
        return self._example_repository

    @property
    def uow(self):
        return self._uow
