from typing import Any, Generic, List, Mapping

from hexagonal.domain import (
    AggregateView,
    GetById,
    TAggregate,
    TEntity,
    TIdEntity,
)
from hexagonal.ports.drivens import (
    IAggregateRepository,
    IEntityRepository,
    ISearchRepository,
    IUnitOfWork,
    TManager,
)

from .handlers import QueryHandler


class SearchAggregateRepository(
    ISearchRepository[
        TManager,
        GetById[TAggregate | TEntity, TIdEntity],
        AggregateView[TAggregate | TEntity],
    ],
    Generic[TManager, TIdEntity, TAggregate, TEntity],
):
    def __init__(
        self,
        repo: IAggregateRepository[TManager, TAggregate, TIdEntity]
        | IEntityRepository[TManager, TEntity, TIdEntity],
    ):
        self._repo = repo

    def search(
        self, query: GetById[TAggregate | TEntity, TIdEntity]
    ) -> List[AggregateView[TAggregate | TEntity]]:
        aggregate = self._repo.get(query.id)
        return [AggregateView[TAggregate | TEntity].new(aggregate)]

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
        GetById[TAggregate | TEntity, TIdEntity],
        AggregateView[TAggregate | TEntity],
    ],
    Generic[TManager, TIdEntity, TAggregate, TEntity],
):
    def __init__(
        self,
        agg_repo: IAggregateRepository[TManager, TAggregate, TIdEntity]
        | IEntityRepository[TManager, TEntity, TIdEntity],
    ):
        search = SearchAggregateRepository(agg_repo)
        super().__init__(search)


class GetAggregateByIdHandler(GetByIdHandler[TManager, TIdEntity, TAggregate, Any]):
    def __init__(self, agg_repo: IAggregateRepository[TManager, TAggregate, TIdEntity]):
        super().__init__(agg_repo)


class GetEntityByIdHandler(GetByIdHandler[TManager, TIdEntity, Any, TEntity]):
    def __init__(self, entity_repo: IEntityRepository[TManager, TEntity, TIdEntity]):
        super().__init__(entity_repo)
