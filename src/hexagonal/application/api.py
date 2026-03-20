# mypy: disable-error-code="misc"
import time
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from eventsourcing.utils import SupportsTopic, get_topic, register_topic

from hexagonal.domain import (
    CloudMessage,
    Command,
    CommandOutcome,
    EventOutcome,
    QueryOne,
    TCommand,
    TEvento,
)
from hexagonal.domain.base import TEvent
from hexagonal.ports.drivens import TAggregate
from hexagonal.ports.drivers import IBaseApplication

from .app import GetEvent
from .query import AggregateView

TBaseApp = TypeVar("TBaseApp", bound=IBaseApplication[Any])


class BaseAPI(Generic[TBaseApp]):
    class Events(Enum):
        @classmethod
        def get_topics(cls) -> list[Tuple[str, SupportsTopic]]:
            topics: list[Tuple[str, SupportsTopic]] = []
            for topic in cls:
                if issubclass(topic.value, TEvento):
                    topics.append((topic.value.TOPIC, topic.value))
                elif issubclass(topic.value, BaseAPI.Events):
                    topics.extend(topic.value.get_topics())
                else:
                    topics.append((get_topic(topic.value), topic.value))
            return topics

    class Commands(Enum):
        @classmethod
        def get_topics(cls) -> list[Tuple[str, SupportsTopic]]:
            topics: list[Tuple[str, SupportsTopic]] = []
            for topic in cls:
                if issubclass(topic.value, Command):
                    topics.append((topic.value.TOPIC, topic.value))
                elif issubclass(topic.value, BaseAPI.Commands):
                    topics.extend(topic.value.get_topics())
                else:
                    topics.append((get_topic(topic.value), topic.value))
            return topics

    class Queries(Enum): ...

    def __init__(self, app: TBaseApp):
        self._app = app
        self.topics = self.Events.get_topics() + self.Commands.get_topics()

    def register_topics(self) -> None:
        for topic_name, topic in self.topics:
            register_topic(topic_name, topic)

    @property
    def app(self) -> TBaseApp:
        return self._app

    def _dispatch_command(
        self,
        command: TCommand,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        default_events: Optional[List[Type[TEvento]]] = None,
        to_outbox: bool = False,
        **kwargs: Any,
    ) -> CommandOutcome[TCommand]:
        """Dispatch a command and optionally await events before returning."""
        cloud_message = CloudMessage[type(command)].new(command, **kwargs)
        if to_outbox:
            self.app.command_bus.dispatch(cloud_message, to_outbox=to_outbox)
            return CommandOutcome(command=cloud_message, events={}, has_events=False)

        tracked_events: set[Type[TEvento]] = set()
        events = events or []
        default_events = default_events or []
        tracked_events.update(events + default_events)
        awaited: Dict[Type[TEvento], GetEvent[TEvento]] = {
            e: GetEvent[e]()  # type: ignore
            for e in tracked_events
        }
        for e, handler in awaited.items():
            self.app.event_bus.wait_for_publish(e, handler)

        self.app.command_bus.dispatch(cloud_message)
        return CommandOutcome(
            command=cloud_message,
            events={event: wrapper.event for event, wrapper in awaited.items()},
        )

    def _get_aggregate(
        self,
        id: UUID,
        query_type: Type[QueryOne[AggregateView[TAggregate]]],
        **kwargs: Any,
    ) -> TAggregate:
        query = query_type.new(id, **kwargs)
        return self.app.query_bus.get(query).item.value

    def publish_and_wait(
        self,
        event: TEvent,
        wait: float | None = None,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        default_events: Optional[List[Type[TEvento]]] = None,
        to_outbox: bool = True,
        **kwargs: Any,
    ) -> EventOutcome[TEvent]:
        """Publish an event and optionally await other events before returning."""
        cloud_message = CloudMessage[type(event)].new(event, **kwargs)

        tracked_events: set[Type[TEvento]] = set()
        events = events or []
        default_events = default_events or []
        tracked_events.update(events + default_events)
        awaited: Dict[Type[TEvento], GetEvent[TEvento]] = {
            e: GetEvent[e]()  # type: ignore
            for e in tracked_events
        }
        for e, handler in awaited.items():
            self.app.event_bus.wait_for_publish(e, handler)

        if to_outbox:
            self.app.event_bus.save_to_outbox(cloud_message)
            self.app.event_bus.publish_from_outbox()
        else:
            self.app.event_bus.publish(cloud_message)

        if wait is not None:
            time.sleep(wait)
        return EventOutcome(
            event=cloud_message,
            events={event: wrapper.event for event, wrapper in awaited.items()},
        )


__all__ = ["CommandOutcome", "EventOutcome", "BaseAPI", "GetEvent", "TBaseApp"]
