# mypy: disable-error-code="misc"
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from hexagonal.domain import CloudMessage, TCommand, TEvent, TEvento
from hexagonal.ports.drivers import IBaseApplication

TBaseApp = TypeVar("TBaseApp", bound=IBaseApplication[Any])


class GetEvent(Generic[TEvent]):
    event: TEvent | None = None

    def __init__(self):
        self.event = None

    def __call__(self, event: TEvent):
        self.event = event


class BaseAPI(Generic[TBaseApp]):
    def __init__(self, app: TBaseApp):
        self._app = app

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
    ) -> Tuple[CloudMessage[TCommand], Dict[Type[TEvento], TEvento | None]]:
        """Dispatch a command and optionally await events before returning."""
        cloud_message = CloudMessage[type(command)].new(command, **kwargs)
        if to_outbox:
            self.app.command_bus.dispatch(cloud_message, to_outbox=to_outbox)
            return cloud_message, {}
        tracked_events: set[Type[TEvento]] = set()
        if events is not None:
            for e in events:
                tracked_events.add(e)
        if default_events is not None:
            for e in default_events:
                tracked_events.add(e)
        awaited: Dict[Type[TEvento], GetEvent[TEvento]] = {}
        for e in tracked_events:
            handler = GetEvent[e]()  # type: ignore
            self.app.event_bus.wait_for_publish(e, handler)
            awaited[e] = handler
        self.app.command_bus.dispatch(cloud_message)
        return cloud_message, {
            event: wrapper.event for event, wrapper in awaited.items()
        }
