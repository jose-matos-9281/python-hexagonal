from abc import abstractmethod
from typing import Generic

from example.contacto.ports.drivens import IAppContactoInfrastructure
from hexagonal.ports.drivens import IBaseInfrastructure, IUnitOfWork, TManager


class IexampleInfrastructure(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def uow(self) -> IUnitOfWork[TManager]: ...

    @property
    @abstractmethod
    def contacto(self) -> IAppContactoInfrastructure[TManager]: ...
