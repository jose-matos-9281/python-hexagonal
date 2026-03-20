from typing import Any, Generic, Type

from .aggregate import TAggregateOrEntity, TIdEntity
from .base import QueryOne, ValueObject


class AggregateView(ValueObject[TAggregateOrEntity]): ...


class GetById(
    QueryOne[AggregateView[TAggregateOrEntity]], Generic[TAggregateOrEntity, TIdEntity]
):
    id: TIdEntity

    @classmethod
    def new(
        cls, id: TIdEntity, agg_type: Type[TAggregateOrEntity], *_: Any, **__: Any
    ) -> "GetById[TAggregateOrEntity, TIdEntity]":
        return cls(
            id=id,
            view=AggregateView[agg_type],  # type: ignore
        )
