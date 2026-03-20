# mypy: disable-error-code="misc"
from typing import Dict, Generic, Literal, Optional, Type, overload

from pydantic import Field

from hexagonal.domain import CloudMessage, Inmutable, TCommand, TEvent, TEvento


class CommandOutcome(Inmutable, Generic[TCommand]):
    command: CloudMessage[TCommand]
    events: Dict[Type[TEvento], TEvento | None] = Field(default_factory=lambda: {})
    has_events: bool = True

    @overload
    def get(
        self, event_type: Type[TEvent], *, raise_error: Literal[True] = True
    ) -> TEvent: ...

    @overload
    def get(
        self, event_type: Type[TEvent], *, raise_error: Literal[False]
    ) -> Optional[TEvent]: ...

    def get(
        self, event_type: Type[TEvent], *, raise_error: bool = True
    ) -> Optional[TEvent]:
        event = self.events.get(event_type)  # type: ignore
        if event is None and raise_error:
            raise KeyError(f"Event {event_type} not found in response")
        elif not isinstance(event, event_type):
            raise TypeError(f"Event {event_type} is not of type {event_type}")
        return event


class EventOutcome(Inmutable, Generic[TEvent]):
    event: CloudMessage[TEvent]
    events: Dict[Type[TEvento], TEvento | None] = Field(default_factory=lambda: {})
    has_events: bool = True

    @overload
    def get(
        self, event_type: Type[TEvent], *, raise_error: Literal[True] = True
    ) -> TEvent: ...

    @overload
    def get(
        self, event_type: Type[TEvent], *, raise_error: Literal[False]
    ) -> Optional[TEvent]: ...

    def get(
        self, event_type: Type[TEvent], *, raise_error: bool = True
    ) -> Optional[TEvent]:
        event = self.events.get(event_type)  # type: ignore
        if event is None and raise_error:
            raise KeyError(f"Event {event_type} not found in response")
        elif not isinstance(event, event_type):
            raise TypeError(f"Event {event_type} is not of type {event_type}")
        return event
