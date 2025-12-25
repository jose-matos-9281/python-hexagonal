from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar, Dict, Generic, Optional, Self, Type, TypeVar
from uuid import UUID

from eventsourcing.domain import CanCreateTimestamp
from pydantic import BaseModel, ConfigDict, Field
from uuid6 import uuid7


class HasTopic:
    TOPIC: ClassVar[str] = ""

    def __init_subclass__(cls, *, topic_suffix: Optional[str] = None, **kwargs: Any):
        # Extraemos nuestro argumento para no pasárselo a Pydantic
        super().__init_subclass__(**kwargs)  # aquí Pydantic recibe sólo lo suyo
        new_topic = topic_suffix or cls.__name__

        # Buscamos el topic base más específico en toda la cadena de herencia
        base_topic = ""
        for base in cls.__mro__[1:]:  # Empezamos desde el padre más inmediato
            if issubclass(base, HasTopic) and hasattr(base, "TOPIC") and base.TOPIC:
                base_topic = base.TOPIC
                break
        actual_topic = cls.TOPIC
        if actual_topic != base_topic:
            set_topic = actual_topic
        else:
            set_topic = f"{base_topic}{'.' if base_topic != '' else ''}{new_topic}"
        cls.TOPIC = set_topic  # type: ignore


class Inmutable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FactoryMethod(ABC):
    @classmethod
    @abstractmethod
    def new(cls, *_: Any, **__: Any) -> Self:
        raise NotImplementedError


class Message(Inmutable, FactoryMethod):
    message_id: UUID = Field(default_factory=uuid7)
    timestamp: datetime = Field(default_factory=CanCreateTimestamp.create_timestamp)


class DomainEvent(Message, HasTopic): ...


class IntegrationEvent(Message, HasTopic): ...


class Command(Message, HasTopic): ...


TValue = TypeVar("TValue")


class ValueObject(Inmutable, FactoryMethod, Generic[TValue]):
    value: TValue

    @classmethod
    def new(cls, value: TValue, *_: Any, **__: Any) -> Self:
        return cls(value=value)


TMessagePayload = IntegrationEvent | Command | DomainEvent

TMessage = TypeVar("TMessage", bound=TMessagePayload)

TMessagePayloadType = TypeVar("TMessagePayloadType", bound=TMessagePayload)


class CloudMessage(Inmutable, FactoryMethod, Generic[TMessage]):
    type: str
    payload: TMessage
    message_id: UUID
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    occurred_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def new(
        cls,
        payload: TMessage,
        *,
        mid: UUID | None = None,
        **kw: Any,
    ) -> "CloudMessage[TMessage]":
        mid = mid or payload.message_id
        return cls(
            type=payload.TOPIC,
            payload=payload,
            occurred_at=payload.timestamp,
            message_id=mid,
            correlation_id=mid,
            metadata=kw,
        )

    def derive(
        self,
        payload: TMessagePayloadType,
        *,
        mid: UUID | None = None,
        **kw: Any,
    ) -> "CloudMessage[TMessagePayloadType]":
        mid = mid or payload.message_id
        return CloudMessage(
            message_id=mid,
            type=payload.TOPIC,
            payload=payload,
            correlation_id=self.correlation_id,
            causation_id=self.message_id,
            metadata=kw,
            occurred_at=payload.timestamp,
        )


TCommand = TypeVar("TCommand", bound=Command)
TEvento = DomainEvent | IntegrationEvent
TEvent = TypeVar("TEvent", bound=TEvento)


class View(Inmutable): ...


TView = TypeVar("TView", bound=ValueObject[Any])


class Query(Inmutable, FactoryMethod, HasTopic, Generic[TView]):
    view: Type[TView]


class QueryResults(Inmutable, Generic[TView], FactoryMethod):
    items: list[TView]
    limit: int
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None

    def __len__(self):
        return len(self.items)

    @classmethod
    def new(
        cls,
        items: list[TView],
        limit: int,
        next_cursor: Optional[str] = None,
        prev_cursor: Optional[str] = None,
    ):
        return cls(
            items=items, limit=limit, next_cursor=next_cursor, prev_cursor=prev_cursor
        )


class QueryResult(Inmutable, Generic[TView], FactoryMethod):
    item: TView

    @classmethod
    def new(cls, item: TView):
        return cls(item=item)


TQuery = TypeVar("TQuery", bound=Query[Any], contravariant=True)
