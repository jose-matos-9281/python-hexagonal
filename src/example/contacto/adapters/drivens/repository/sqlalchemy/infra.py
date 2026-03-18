from uuid import UUID

from eventsourcing.persistence import Mapper

from example.contacto.ports.drivens import IAppContactoInfrastructure
from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyUnitOfWork,
)
from hexagonal.application import InfrastructureGroup

from .contacto import SQLAlchemyContactoRepositoryAdapter
from .entidad import SQLAlchemyEntidadRepositoryAdapter
from .entidad_contacto import SQLAlchemyEntidadContactoRepositoryAdapter


class SQLAlchemyContactoAppInfrastructure(
    IAppContactoInfrastructure[SQLAlchemyConnectionContextManager],
    InfrastructureGroup,
):
    def __init__(
        self,
        manager: SQLAlchemyConnectionContextManager,
        mapper: Mapper[UUID],
        uow: SQLAlchemyUnitOfWork | None = None,
    ):
        self._contacto_repository = SQLAlchemyContactoRepositoryAdapter(
            mapper,
            manager,
        )
        self._entidad_contacto_repository = SQLAlchemyEntidadContactoRepositoryAdapter(
            mapper,
            manager,
        )
        self._uow = uow or SQLAlchemyUnitOfWork(
            self._contacto_repository, self._entidad_contacto_repository
        )
        self._entidad_repository = SQLAlchemyEntidadRepositoryAdapter(mapper, manager)
        if uow is None:
            return super().__init__(self._uow)

        return super().__init__(
            self._contacto_repository,
            self._entidad_contacto_repository,
            self._entidad_repository,
        )

    @property
    def contacto_repository(self):
        return self._contacto_repository

    @property
    def entidad_contacto_repository(self):
        return self._entidad_contacto_repository

    @property
    def uow(self):
        return self._uow

    @property
    def entidad_repository(self):
        return self._entidad_repository
