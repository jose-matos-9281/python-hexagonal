# pyright: reportMissingTypeStubs=false, reportUnknownArgumentType=false, reportMissingParameterType=none, reportGeneralTypeIssues=none

from typing import (
    Any,
    ClassVar,
    Dict,
    Mapping,
    Type,
    TypeVar,
    get_args,
    get_origin,
)
from uuid import UUID

from eventsourcing.persistence import Mapper
from eventsourcing.utils import Environment

from hexagonal.application import Infrastructure
from hexagonal.domain import AggregateRoot, TIdEntity
from hexagonal.ports.drivens import (
    IAggregateRepository,
    IBaseRepository,
    IUnitOfWork,
    TManager,
)

TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any, Any])


class BaseRepositoryAdapter(IBaseRepository[TManager], Infrastructure):
    ENV: ClassVar[Dict[str, str]] = {}
    NAME: ClassVar[str | None] = None

    def __init__(self, connection_manager: TManager):
        super().__init__()
        self._connection_manager = connection_manager

    def initialize(self, env: Mapping[str, str]) -> None:
        env2 = self.ENV.copy()
        name = self.NAME or self.__class__.__name__.upper()
        env2.update(env)
        self.env = Environment(name, env2)
        self._attached_to_uow = False
        self._manager_at_uow: TManager | None = None
        super().initialize(self.env)

    def attach_to_unit_of_work(self, uow: IUnitOfWork[TManager]) -> None:
        self._attached_to_uow = True
        self._manager_at_uow = uow.connection_manager

    def detach_from_unit_of_work(self) -> None:
        self._attached_to_uow = False
        self._manager_at_uow = None

    @property
    def connection_manager(self) -> TManager:
        if self._attached_to_uow and self._manager_at_uow is not None:
            return self._manager_at_uow
        return self._connection_manager


class BaseAggregateRepositoryAdapter(
    BaseRepositoryAdapter[TManager],
    IAggregateRepository[TManager, TAggregate, TIdEntity],
):
    _type_of_aggregate: Type[TAggregate]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        # Inspect generic base to find the concrete type argument
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base)
            if origin and issubclass(origin, BaseAggregateRepositoryAdapter):
                args = get_args(base)
                if args:
                    cls._type_of_aggregate = args[0]
                    cls.NAME = cls._type_of_aggregate.__name__.upper()

    def __init__(self, mapper: Mapper[UUID], connection_manager: TManager):
        super().__init__(connection_manager)
        self._mapper = mapper

    @property
    def aggregate_name(self) -> str:
        return self._type_of_aggregate.__name__
