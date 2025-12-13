from typing import Any, Generic, List, Mapping, Type

from hexagonal.application.handlers import QueryHandler
from hexagonal.domain import Query, TIdEntity, ValueObject
from hexagonal.ports.drivens import (
    IAggregateRepository,
    ISearchRepository,
    TAggregate,
    TManager,
)
from hexagonal.ports.drivens.repository import IUnitOfWork


class AggregateView(ValueObject[TAggregate]): ...


class GetById(Query[AggregateView[TAggregate]], Generic[TAggregate, TIdEntity]):
    id: TIdEntity

    @classmethod
    def new(cls, id: TIdEntity, agg_type: Type[TAggregate], *_: Any, **__: Any):
        return cls(id=id, view=AggregateView[agg_type])  # type: ignore


class SearchAggregateRepository(
    ISearchRepository[
        TManager,
        GetById[TAggregate, TIdEntity],
        AggregateView[TAggregate],
    ],
    Generic[TManager, TAggregate, TIdEntity],
):
    def __init__(self, repo: IAggregateRepository[TManager, TAggregate, TIdEntity]):
        self._repo = repo

    def search(
        self, query: GetById[TAggregate, TIdEntity]
    ) -> List[AggregateView[TAggregate]]:
        aggregate = self._repo.get(query.id)
        return [AggregateView[TAggregate].new(aggregate)]

    ## decorate methods from IAggregateRepository to pass through initialization ##
    def initialize(self, env: Mapping[str, str]) -> None:
        self._repo.initialize(env)

    @property
    def initialized(self):
        return self._repo.initialized

    @property
    def connection_manager(self) -> TManager:
        return self._repo.connection_manager

    def attach_to_unit_of_work(self, uow: IUnitOfWork[TManager]) -> None:
        self._repo.attach_to_unit_of_work(uow)

    def detach_from_unit_of_work(self) -> None:
        self._repo.detach_from_unit_of_work()


class GetByIdHandler(
    QueryHandler[
        TManager,
        GetById[TAggregate, TIdEntity],
        AggregateView[TAggregate],
    ],
    Generic[TManager, TAggregate, TIdEntity],
):
    def __init__(self, agg_repo: IAggregateRepository[TManager, TAggregate, TIdEntity]):
        search = SearchAggregateRepository(agg_repo)
        super().__init__(search)
