from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

import orjson
from eventsourcing.persistence import (
    Mapper,
    Transcoder,
)
from eventsourcing.utils import get_topic, resolve_topic

from hexagonal.domain import (
    CloudMessage,
    Command,
    DomainEvent,
    IntegrationEvent,
)


@dataclass
class StoredMessage:
    topic: str
    state: bytes


TMessage = Command | DomainEvent | IntegrationEvent | CloudMessage[Any]


class MessageMapper(Mapper[UUID]):
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
