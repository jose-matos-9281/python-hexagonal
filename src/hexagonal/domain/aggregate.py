from abc import abstractmethod
from datetime import datetime
from typing import Any, Generic, List, Self, Type, TypeVar, get_args, get_origin
from uuid import UUID

from eventsourcing.domain import (
    AggregateCreated,
    AggregateEvent,
    BaseAggregate,
    CanMutateAggregate,
    Snapshot,
    event,
)
from uuid6 import uuid7

from .base import Inmutable, ValueObject

command = event


class IdValueObject(ValueObject[UUID]):
    @classmethod
    def new(cls, *_: Any, **__: Any) -> Self:
        return cls(value=uuid7())


TIdEntity = TypeVar("TIdEntity", bound=IdValueObject)


class AggregateState(Inmutable, Generic[TIdEntity]):
    id: TIdEntity
    agg_version: int
    agg_unsaved_commands: List[CanMutateAggregate[Any]]
    created_on: datetime
    modified_on: datetime

    @classmethod
    def from_aggregate(
        cls, aggregate: "AggregateRoot[TIdEntity]", **kwargs: Any
    ) -> Self:
        return cls(
            id=aggregate.value_id,
            agg_version=aggregate.version,
            agg_unsaved_commands=aggregate.pending_events,
            created_on=aggregate.created_on,
            modified_on=aggregate.modified_on,
            **kwargs,
        )


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

    @event(Deleted)
    def delete(self) -> None:
        pass

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

    @property
    @abstractmethod
    def state(self) -> AggregateState[TIdEntity]: ...
