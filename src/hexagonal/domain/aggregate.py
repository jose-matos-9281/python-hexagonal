from typing import Any, Generic, Self, Type, TypeVar, get_args, get_origin
from uuid import UUID

from eventsourcing.domain import (
    AggregateCreated,
    AggregateEvent,
    BaseAggregate,
    Snapshot,
    event,
)
from uuid6 import uuid7

from .base import ValueObject

command = event


class IdValueObject(ValueObject[UUID]):
    @classmethod
    def new(cls, *_: Any, **__: Any) -> Self:
        return cls(value=uuid7())


TIdEntity = TypeVar("TIdEntity", bound=IdValueObject)


class AggregateRoot(BaseAggregate[UUID], Generic[TIdEntity]):
    _id_type: Type[TIdEntity]

    class Event(AggregateEvent):
        pass

    class Created(Event, AggregateCreated):
        pass

    class Deleted(Event):
        def mutate(self, aggregate: Any) -> Any:
            super().mutate(aggregate)
            return None

    Snapshot = Snapshot

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        # Inspect generic base to find the concrete type argument
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base)
            if issubclass(origin, AggregateRoot):
                args = get_args(base)
                if args:
                    cls._id_type = args[0]

    @classmethod
    def create_id(cls, *args: Any, **kwargs: Any):
        return cls._id_type.new(*args, **kwargs).value

    @property
    def value_id(self) -> TIdEntity:
        # Instantiate the captured type using the stored `id` value
        try:
            return self._id_type(value=self.id)
        except Exception as e:
            raise ValueError(
                f"Cannot instantiate {self._id_type} with value {self.id}: {e}"
            ) from e

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AggregateRoot):
            return False
        return self.value_id == other.value_id  # type: ignore

    def __hash__(self) -> int:
        return hash(self.value_id)
