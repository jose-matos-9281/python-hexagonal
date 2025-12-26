from datetime import datetime
from typing import (
    Any,
    Generic,
    Self,
    Type,
    TypeVar,
    get_args,
    get_origin,
)
from uuid import UUID

from eventsourcing.domain import (
    AggregateCreated,
    AggregateEvent,
    BaseAggregate,
    CanSnapshotAggregate,
    MutableOrImmutableAggregate,
    event,
)
from eventsourcing.utils import get_topic
from pydantic import ConfigDict, TypeAdapter
from uuid6 import uuid7

from .base import Inmutable, ValueObject

command = event


class IdValueObject(ValueObject[UUID]):
    @classmethod
    def new(cls, *_: Any, **__: Any) -> Self:
        return cls(value=uuid7())


TIdEntity = TypeVar("TIdEntity", bound=IdValueObject)
datetime_adapter = TypeAdapter(datetime)


class SnapshotState(Inmutable, Generic[TIdEntity]):
    model_config = ConfigDict(extra="allow")
    id: TIdEntity
    created_on: datetime
    modified_on: datetime

    def __init__(self, **kwargs: Any) -> None:
        for key in ["_created_on", "_modified_on"]:
            kwargs[key.removeprefix("_")] = datetime_adapter.validate_python(
                kwargs[key]
            )
        super().__init__(**kwargs)


TSnapshotState = TypeVar("TSnapshotState", bound=SnapshotState[Any])


class AggregateSnapshot(Inmutable, CanSnapshotAggregate[UUID], Generic[TSnapshotState]):
    originator_id: UUID
    originator_version: int
    timestamp: datetime
    topic: str
    state: TSnapshotState

    @classmethod
    def take(
        cls,
        aggregate: MutableOrImmutableAggregate[UUID],
    ) -> Self:
        """Creates a snapshot of the given :class:`Aggregate` object."""
        aggregate_state = dict(aggregate.__dict__)
        class_version = getattr(type(aggregate), "class_version", 1)
        if class_version > 1:
            aggregate_state["class_version"] = class_version
        if isinstance(aggregate, AggregateRoot):
            aggregate.complete_snapshot_state(aggregate_state)
            aggregate_state.pop("_id")
            aggregate_state.pop("_version")
            aggregate_state.pop("_pending_events")
        dict_snap = dict(
            originator_id=aggregate.id,  # type: ignore[call-arg]
            originator_version=aggregate.version,  # pyright: ignore[reportCallIssue]
            timestamp=cls.create_timestamp(),  # pyright: ignore[reportCallIssue]
            topic=get_topic(type(aggregate)),  # type: ignore[call-arg]
            state=aggregate_state,  # pyright: ignore[reportCallIssue]
        )
        return cls.model_validate(dict_snap)


class AggregateRoot(BaseAggregate[UUID], Generic[TIdEntity, TSnapshotState]):
    _id_type: Type[TIdEntity]

    Snapshot: Type[AggregateSnapshot[TSnapshotState]]

    class Event(AggregateEvent):
        pass

    class Created(Event, AggregateCreated):
        pass

    class Deleted(Event):
        def mutate(self, aggregate: Any) -> Any:
            super().mutate(aggregate)
            return None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Inspect generic base to find the concrete type argument
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base)
            if issubclass(origin, AggregateRoot):
                args = get_args(base)
                if args:
                    cls._id_type = args[0]
                    state_type = args[1]

                    cls.Snapshot = AggregateSnapshot[state_type]  # type: ignore[valid-type]

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

    def complete_snapshot_state(self, state: dict[str, Any]) -> dict[str, Any]:
        state["id"] = self.value_id
        return state

    @property
    def state(self) -> TSnapshotState:
        return self.Snapshot.take(self).state

    @classmethod
    def reconstruct_from_snapshot(
        cls,
        snapshot: AggregateSnapshot[TSnapshotState],
    ) -> Self:
        agg = snapshot.mutate(None)
        assert isinstance(agg, cls)
        return agg

    def take_snapshot(self) -> AggregateSnapshot[TSnapshotState]:
        return self.Snapshot.take(self)
