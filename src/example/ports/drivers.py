from abc import abstractmethod

from example.ports.drivens import IAppExampleInfrastructure
from hexagonal.ports.drivens import TManager
from hexagonal.ports.drivers import IBusApp


class IExampleApp(IBusApp[TManager]):
    @property
    @abstractmethod
    def infrastructure(self) -> IAppExampleInfrastructure[TManager]: ...
