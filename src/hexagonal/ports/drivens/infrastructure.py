from abc import ABC, abstractmethod
from typing import Mapping

from hexagonal.domain import InfrastructureNotInitialized


class IBaseInfrastructure(ABC):
    @property
    @abstractmethod
    def initialized(self) -> bool: ...

    @abstractmethod
    def initialize(self, env: Mapping[str, str]) -> None: ...

    def verify(self):
        if not self.initialized:
            raise InfrastructureNotInitialized(
                f"{self.__class__.__name__} is not initialized"
            )
