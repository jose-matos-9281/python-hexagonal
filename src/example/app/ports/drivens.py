from abc import abstractmethod
from typing import Generic

from example.contacto.ports.drivens import (
    IAppContactoInfrastructure,
    IContactoRepository,
    IContactoWriteScope,
    IEntidadContactoRepository,
    IEntidadRepository,
)
from hexagonal.ports.drivens import (
    IBaseInfrastructure,
    IInboxRepository,
    IOutboxRepository,
    IReadScopeFactory,
    IReadScopeRunner,
    IUnitOfWork,
    IWriteScopeFactory,
    IWriteScopeRunner,
    TManager,
)


class IexampleInfrastructure(
    IBaseInfrastructure,
    IWriteScopeFactory[IContactoWriteScope[TManager]],
    IReadScopeFactory[TManager],
    Generic[TManager],
):
    @property
    @abstractmethod
    def uow(self) -> IUnitOfWork[TManager]: ...

    @property
    @abstractmethod
    def contacto(self) -> IAppContactoInfrastructure[TManager]: ...

    @property
    @abstractmethod
    def write_scope_runner(
        self,
    ) -> IWriteScopeRunner[IContactoWriteScope[TManager]]: ...

    @property
    @abstractmethod
    def read_scope_runner(self) -> IReadScopeRunner[TManager]: ...

    @abstractmethod
    def build_contacto_repository(
        self, manager: TManager
    ) -> IContactoRepository[TManager]: ...

    @abstractmethod
    def build_entidad_repository(
        self, manager: TManager
    ) -> IEntidadRepository[TManager]: ...

    @abstractmethod
    def build_entidad_contacto_repository(
        self, manager: TManager
    ) -> IEntidadContactoRepository[TManager]: ...

    @abstractmethod
    def build_inbox_repository(
        self, manager: TManager
    ) -> IInboxRepository[TManager]: ...

    @abstractmethod
    def build_outbox_repository(
        self, manager: TManager
    ) -> IOutboxRepository[TManager]: ...
