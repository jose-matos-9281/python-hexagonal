from abc import abstractmethod

from example.contacto.ports.drivens import IAppContactoInfrastructure
from hexagonal.ports.drivens import TManager
from hexagonal.ports.drivers import IBusApp


class IContactoApp(IBusApp[TManager]):
    @property
    @abstractmethod
    def infrastructure(self) -> IAppContactoInfrastructure[TManager]: ...
