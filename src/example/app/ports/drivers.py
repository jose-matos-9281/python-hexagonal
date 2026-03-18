from abc import abstractmethod

from example.app.ports.drivens import IexampleInfrastructure
from hexagonal.application import ComposableBusApp
from hexagonal.ports.drivens import TManager


class IexampleApp(ComposableBusApp[TManager]):
    @property
    @abstractmethod
    def infrastructure(self) -> IexampleInfrastructure[TManager]: ...
