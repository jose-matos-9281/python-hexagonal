from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from eventsourcing.persistence import Mapper

from example.app.ports.drivens import IexampleInfrastructure
from example.contacto.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyContactoAppInfrastructure,
    SQLAlchemyContactoRepositoryAdapter,
    SQLAlchemyEntidadContactoRepositoryAdapter,
    SQLAlchemyEntidadRepositoryAdapter,
)
from hexagonal.application import (
    Infrastructure,
)
from hexagonal.integrations.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyDatastore,
    SQLAlchemyInboxRepository,
    SQLAlchemyOutboxRepository,
    SQLAlchemyScopeRunner,
    SQLAlchemyUnitOfWork,
)


@dataclass(frozen=True)
class ExampleSQLAlchemyWriteScope:
    uow: SQLAlchemyUnitOfWork
    contacto_repository: SQLAlchemyContactoRepositoryAdapter
    entidad_repository: SQLAlchemyEntidadRepositoryAdapter
    entidad_contacto_repository: SQLAlchemyEntidadContactoRepositoryAdapter
    inbox_repository: SQLAlchemyInboxRepository
    outbox_repository: SQLAlchemyOutboxRepository


class exampleSQLAlchemyInfrastructure(
    IexampleInfrastructure[SQLAlchemyConnectionContextManager], Infrastructure
):
    def __init__(
        self,
        mapper: Mapper[UUID],
        datastore: SQLAlchemyDatastore,
    ):
        super().__init__()
        self._mapper = mapper
        self._datastore = datastore
        self._env: Mapping[str, str] = {}
        self._scope_runner = SQLAlchemyScopeRunner(
            self.create_write_scope,
            self.create_read_scope,
        )
        self._uow: SQLAlchemyUnitOfWork | None = None
        self._contacto: SQLAlchemyContactoAppInfrastructure | None = None

    def initialize(self, env: Mapping[str, str]) -> None:
        self._env = dict(env)
        compatibility_manager = self.create_read_scope()
        self._uow = SQLAlchemyUnitOfWork(connection_manager=compatibility_manager)
        self._uow.initialize(self._env)
        self._contacto = SQLAlchemyContactoAppInfrastructure(
            compatibility_manager,
            self._mapper,
            self._uow,
        )
        self._contacto.initialize(self._env)
        self._initialized = True

    def create_read_scope(self) -> SQLAlchemyConnectionContextManager:
        return SQLAlchemyConnectionContextManager(self._datastore)

    def build_contacto_repository(
        self, manager: SQLAlchemyConnectionContextManager
    ) -> SQLAlchemyContactoRepositoryAdapter:
        repository = SQLAlchemyContactoRepositoryAdapter(self._mapper, manager)
        repository.initialize(self._env)
        return repository

    def build_entidad_repository(
        self, manager: SQLAlchemyConnectionContextManager
    ) -> SQLAlchemyEntidadRepositoryAdapter:
        repository = SQLAlchemyEntidadRepositoryAdapter(self._mapper, manager)
        repository.initialize(self._env)
        return repository

    def build_entidad_contacto_repository(
        self, manager: SQLAlchemyConnectionContextManager
    ) -> SQLAlchemyEntidadContactoRepositoryAdapter:
        repository = SQLAlchemyEntidadContactoRepositoryAdapter(self._mapper, manager)
        repository.initialize(self._env)
        return repository

    def build_inbox_repository(
        self, manager: SQLAlchemyConnectionContextManager
    ) -> SQLAlchemyInboxRepository:
        repository = SQLAlchemyInboxRepository(self._mapper, manager)
        repository.initialize(self._env)
        return repository

    def build_outbox_repository(
        self, manager: SQLAlchemyConnectionContextManager
    ) -> SQLAlchemyOutboxRepository:
        repository = SQLAlchemyOutboxRepository(self._mapper, manager)
        repository.initialize(self._env)
        return repository

    def create_write_scope(self) -> ExampleSQLAlchemyWriteScope:
        manager = self.create_read_scope()
        contacto_repository = self.build_contacto_repository(manager)
        entidad_repository = self.build_entidad_repository(manager)
        entidad_contacto_repository = self.build_entidad_contacto_repository(manager)
        inbox_repository = self.build_inbox_repository(manager)
        outbox_repository = self.build_outbox_repository(manager)
        uow = SQLAlchemyUnitOfWork(
            contacto_repository,
            entidad_repository,
            entidad_contacto_repository,
            inbox_repository,
            outbox_repository,
            connection_manager=manager,
        )
        if self._env:
            uow.initialize(self._env)
        return ExampleSQLAlchemyWriteScope(
            uow=uow,
            contacto_repository=contacto_repository,
            entidad_repository=entidad_repository,
            entidad_contacto_repository=entidad_contacto_repository,
            inbox_repository=inbox_repository,
            outbox_repository=outbox_repository,
        )

    @property
    def uow(self) -> SQLAlchemyUnitOfWork:
        if self._uow is None:
            raise RuntimeError("Example infrastructure not initialized")
        return self._uow

    @property
    def contacto(self) -> SQLAlchemyContactoAppInfrastructure:
        if self._contacto is None:
            raise RuntimeError("Example infrastructure not initialized")
        return self._contacto

    @property
    def write_scope_runner(
        self,
    ) -> SQLAlchemyScopeRunner[
        ExampleSQLAlchemyWriteScope, SQLAlchemyConnectionContextManager
    ]:
        return self._scope_runner

    @property
    def read_scope_runner(
        self,
    ) -> SQLAlchemyScopeRunner[
        ExampleSQLAlchemyWriteScope, SQLAlchemyConnectionContextManager
    ]:
        return self._scope_runner
