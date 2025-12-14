import os
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
)

from eventsourcing.utils import Environment

T = TypeVar("T", covariant=True)


class Entrypoint(ABC, Generic[T]):
    env: ClassVar[Mapping[str, str]] = {}
    name: ClassVar[str]

    @classmethod
    def setName(cls, name: str | None = None):
        if hasattr(cls, "name"):
            return
        cls.name = name or cls.__name__

    @classmethod
    @abstractmethod
    def get(cls, env: Optional[Mapping[str, str]] = None) -> T: ...

    @classmethod
    def strategy(cls) -> Dict[str, Callable[[Optional[Mapping[str, str]]], T]]:
        cls.setName()
        return {cls.name: cls.get}

    @classmethod
    def construct_env(cls, env: Optional[Mapping[str, str]] = None) -> Environment:
        """Constructs environment from which application will be configured."""
        cls.setName()
        _env = dict(cls.env)
        _env.update(os.environ)
        if env is not None:
            _env.update(env)
        return Environment(cls.name, _env)


class EntrypointGroup(Entrypoint[T]):
    env_key: ClassVar[str]
    entrypoints: List[Type[Entrypoint[T]]]

    def __init_subclass__(
        cls,
        **kwargs: Any,
    ):
        super().__init_subclass__(**kwargs)
        cls.name = getattr(cls, "name", cls.__name__)
        env_key = getattr(cls, "env_key", None)
        if not env_key:
            raise ValueError("env_key is required")
        entrypoints = getattr(cls, "entrypoints", None)
        if not entrypoints:
            raise ValueError("entrypoints is required")
        cls.env_key = env_key
        cls.entrypoints = entrypoints

    @classmethod
    def addEntrypoint(cls, entrypoint: Type[Entrypoint[T]]):
        cls.entrypoints.append(entrypoint)

    @classmethod
    def strategy(cls) -> Dict[str, Callable[[Optional[Mapping[str, str]]], T]]:
        strategies: Dict[str, Callable[[Optional[Mapping[str, str]]], T]] = {}
        for entrypoint in cls.entrypoints:
            strategies.update(entrypoint.strategy())
        return strategies

    @classmethod
    def getEntrypoint(
        cls, env: Optional[Mapping[str, str]] = None
    ) -> Type[Entrypoint[T]]:
        env = cls.construct_env(env)
        entrypoint_name = env.get(cls.env_key)
        if entrypoint_name is None:
            raise ValueError(f"Missing entrypoint name: {cls.env_key}")
        entrypoint = next(
            (ep for ep in cls.entrypoints if ep.name == entrypoint_name), None
        )
        if entrypoint is None:
            raise ValueError(f"Unknown entrypoint: {entrypoint_name}")
        return entrypoint

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None) -> T:
        env = cls.construct_env(env)
        strategy = cls.strategy()
        entrypoint_name = env.get(cls.env_key)
        if entrypoint_name is None:
            raise ValueError(f"Missing entrypoint name: {cls.env_key}")
        if entrypoint_name not in strategy:
            raise ValueError(f"Unknown entrypoint: {entrypoint_name}")
        return strategy[entrypoint_name](env)
