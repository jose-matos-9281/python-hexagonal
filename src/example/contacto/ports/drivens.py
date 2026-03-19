from abc import abstractmethod
from typing import Generic

from example.contacto.domain.contacto import Contacto
from example.contacto.domain.entidad import Entidad
from example.contacto.domain.entidad_contacto import (
    EntidadContacto,
    IdEntidadContacto,
)
from example.contacto.domain.shared import IdContacto, IdEntidad
from hexagonal.ports.drivens import (
    IAggregateRepository,
    IBaseInfrastructure,
    IEntityRepository,
    IUnitOfWork,
    TManager,
)

IEntidadContactoRepository = IAggregateRepository[
    TManager, EntidadContacto, IdEntidadContacto
]


IContactoRepository = IAggregateRepository[TManager, Contacto, IdContacto]

IEntidadRepository = IEntityRepository[TManager, Entidad, IdEntidad]


class IAppContactoInfrastructure(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def contacto_repository(self) -> IContactoRepository[TManager]: ...

    @property
    @abstractmethod
    def entidad_contacto_repository(self) -> IEntidadContactoRepository[TManager]: ...

    @property
    @abstractmethod
    def uow(self) -> IUnitOfWork[TManager]: ...

    @property
    @abstractmethod
    def entidad_repository(self) -> IEntidadRepository[TManager]: ...
