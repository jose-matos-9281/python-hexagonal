from dataclasses import dataclass
from typing import Any, Hashable, cast
from uuid import UUID

import orjson
from eventsourcing.domain import DomainEventProtocol
from eventsourcing.persistence import (
    Mapper,
    MapperDeserialisationError,
    StoredEvent,
    Transcoder,
    find_id_convertor,
)
from eventsourcing.utils import get_topic, resolve_topic

from hexagonal.domain import (
    CloudMessage,
    Command,
    DomainEvent,
    IntegrationEvent,
)
from hexagonal.domain.aggregate import AggregateSnapshot
from hexagonal.domain.base import Inmutable


@dataclass
class StoredMessage:
    topic: str
    state: bytes


TMessage = Command | DomainEvent | IntegrationEvent | CloudMessage[Any]


class MessageMapper(Mapper[UUID]):
    def to_stored_event(self, domain_event: DomainEventProtocol[UUID]) -> StoredEvent:
        """Converts the given domain event to a :class:`StoredEvent` object."""
        topic = get_topic(domain_event.__class__)
        event_state = (
            domain_event.model_dump(mode="json")
            if isinstance(domain_event, Inmutable)
            else domain_event.__dict__.copy()
        )
        originator_id = event_state.pop("originator_id")
        originator_version = event_state.pop("originator_version")
        class_version = getattr(type(domain_event), "class_version", 1)
        if class_version > 1:
            event_state["class_version"] = class_version
        stored_state = self.transcoder.encode(event_state)
        if self.compressor:
            stored_state = self.compressor.compress(stored_state)
        if self.cipher:
            stored_state = self.cipher.encrypt(stored_state)
        return StoredEvent(
            originator_id=originator_id,
            originator_version=originator_version,
            topic=topic,
            state=stored_state,
        )

    def to_domain_event(self, stored_event: StoredEvent) -> DomainEventProtocol[UUID]:
        """Converts the given :class:`StoredEvent` to a domain event object."""
        cls = resolve_topic(stored_event.topic)

        stored_state = stored_event.state
        try:
            if self.cipher:
                stored_state = self.cipher.decrypt(stored_state)
            if self.compressor:
                stored_state = self.compressor.decompress(stored_state)
            event_state: dict[str, Any] = self.transcoder.decode(stored_state)
        except Exception as e:
            msg = (
                f"Failed to deserialise state of stored event with "
                f"topic '{stored_event.topic}', "
                f"originator_id '{stored_event.originator_id}' and "
                f"originator_version {stored_event.originator_version}: {e}"
            )
            raise MapperDeserialisationError(msg) from e

        id_convertor = find_id_convertor(
            cls, cast(Hashable, type(stored_event.originator_id))
        )
        # print("ID of convertor:", id(convertor))
        event_state["originator_id"] = id_convertor(stored_event.originator_id)
        event_state["originator_version"] = stored_event.originator_version
        class_version = getattr(cls, "class_version", 1)
        from_version = event_state.pop("class_version", 1)
        while from_version < class_version:
            getattr(cls, f"upcast_v{from_version}_v{from_version + 1}")(event_state)
            from_version += 1
        if issubclass(cls, AggregateSnapshot):
            return cls.model_validate(event_state)  # type: ignore[return-value]
        domain_event = object.__new__(cls)
        domain_event.__dict__.update(event_state)
        return domain_event

    def to_stored_message(self, message: TMessage) -> StoredMessage:
        topic = get_topic(message.__class__)
        event_state = message.model_dump(mode="json")
        stored_state = self.transcoder.encode(event_state)
        if self.compressor:
            stored_state = self.compressor.compress(stored_state)
        if self.cipher:
            stored_state = self.cipher.encrypt(stored_state)
        return StoredMessage(
            topic=topic,
            state=stored_state,
        )

    def to_message(self, stored_message: StoredMessage) -> TMessage:
        stored_state = stored_message.state
        if self.cipher:
            stored_state = self.cipher.decrypt(stored_state)
        if self.compressor:
            stored_state = self.compressor.decompress(stored_state)
        event_state: dict[str, Any] = self.transcoder.decode(stored_state)
        cls = cast(TMessage, resolve_topic(stored_message.topic))
        return cls.model_validate(event_state)


class OrjsonTranscoder(Transcoder):
    def encode(self, obj: Any) -> bytes:
        return orjson.dumps(obj)

    def decode(self, data: bytes) -> Any:
        return orjson.loads(data)
