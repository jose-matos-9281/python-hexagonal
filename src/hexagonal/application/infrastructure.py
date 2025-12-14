from logging import getLogger
from typing import Mapping

from hexagonal.ports.drivens import IBaseInfrastructure

logger = getLogger(__name__)


class ComposableInfrastructure(IBaseInfrastructure):
    def __init__(self, infrastructure: IBaseInfrastructure):
        self.infrastructure = infrastructure

    def initialize(self, env: Mapping[str, str]) -> None:
        self.infrastructure.initialize(env)

    @property
    def initialized(self) -> bool:
        return self.infrastructure.initialized

    def __or__(self, other: IBaseInfrastructure) -> "ComposableInfrastructure":
        other_is_root = (
            other.infrastructures if isinstance(other, InfrastructureGroup) else [other]
        )

        self_is_root = (
            self.infrastructures if isinstance(self, InfrastructureGroup) else [self]
        )
        return InfrastructureGroup(*self_is_root, *other_is_root)

    def __add__(self, other: IBaseInfrastructure) -> "ComposableInfrastructure":
        return self.__or__(other)

    def __and__(self, other: IBaseInfrastructure) -> "ComposableInfrastructure":
        return InfrastructureGroup(self, other)


class InfrastructureGroup(ComposableInfrastructure):
    def __init__(self, *infrastructures: IBaseInfrastructure):
        self.infrastructures = list(infrastructures)

    def initialize(self, env: Mapping[str, str]) -> None:
        for infrastructure in self.infrastructures:
            if infrastructure.initialized:
                continue
            infrastructure.initialize(env)

    @property
    def initialized(self) -> bool:
        return all(
            infrastructure.initialized for infrastructure in self.infrastructures
        )


class Infrastructure(ComposableInfrastructure):
    def __init__(self):
        self._initialized = False

    def initialize(self, env: Mapping[str, str]) -> None:
        logger.debug(f"Initializing {self.__class__.__name__}")
        self._initialized = True

    @property
    def initialized(self) -> bool:
        return self._initialized
