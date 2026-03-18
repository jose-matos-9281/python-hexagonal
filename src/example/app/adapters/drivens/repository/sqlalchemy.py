from uuid import UUID

from eventsourcing.persistence import Mapper

from example.app.ports.drivens import IexampleInfrastructure
from example.contacto.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyContactoAppInfrastructure,
)
from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyUnitOfWork,
)
from hexagonal.application import ComposableInfrastructure, InfrastructureGroup


class exampleSQLAlchemyInfrastructure(
    IexampleInfrastructure[SQLAlchemyConnectionContextManager], InfrastructureGroup
):
    def __init__(
        self,
        mapper: Mapper[UUID],
        manager: SQLAlchemyConnectionContextManager,
        uow: SQLAlchemyUnitOfWork | None = None,
    ):
        self._uow = uow or SQLAlchemyUnitOfWork(connection_manager=manager)
        self._contacto = SQLAlchemyContactoAppInfrastructure(manager, mapper, self._uow)
        infra: ComposableInfrastructure = self._contacto
        if uow is None:
            infra = infra & self._uow
        super().__init__(infra)

    @property
    def uow(self) -> SQLAlchemyUnitOfWork:
        return self._uow

    @property
    def contacto(self) -> SQLAlchemyContactoAppInfrastructure:
        return self._contacto
