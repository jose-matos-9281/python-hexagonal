from example.contacto.ports.drivens import IAppContactoInfrastructure
from hexagonal.adapters.drivens.mappers import MessageMapper
from hexagonal.application import InfrastructureGroup
from hexagonal.integrations.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyUnitOfWork,
)

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
        mapper: MessageMapper,
        uow: SQLAlchemyUnitOfWork | None = None,
    ) -> None:
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
    def contacto_repository(self) -> SQLAlchemyContactoRepositoryAdapter:
        return self._contacto_repository

    @property
    def entidad_contacto_repository(self) -> SQLAlchemyEntidadContactoRepositoryAdapter:
        return self._entidad_contacto_repository

    @property
    def uow(self) -> SQLAlchemyUnitOfWork:
        return self._uow

    @property
    def entidad_repository(self) -> SQLAlchemyEntidadRepositoryAdapter:
        return self._entidad_repository
