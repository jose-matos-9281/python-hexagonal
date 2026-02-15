from typing import Any, Generic, Type

from .aggregate import TAggregate, TIdEntity
from .base import Query, ValueObject


class AggregateView(ValueObject[TAggregate]): ...


class GetById(Query[AggregateView[TAggregate]], Generic[TAggregate, TIdEntity]):
    id: TIdEntity

    @classmethod
    def new(cls, id: TIdEntity, agg_type: Type[TAggregate], *_: Any, **__: Any):
        return cls(id=id, view=AggregateView[agg_type])  # type: ignore
