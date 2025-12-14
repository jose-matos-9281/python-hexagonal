import logging
from typing import Any, Callable, Dict, List, Mapping, Type, overload

from eventsourcing.utils import TopicError, get_topic, strtobool

from hexagonal.domain import (
    CloudMessage,
    HandlerAlreadyRegistered,
    HandlerNotRegistered,
    TEvent,
    TEvento,
)
from hexagonal.ports.drivens import IEventBus, IMessageHandler, TManager

from .message_bus import MessageBus
from .utils import EVENT_BUS_RAISE_ERROR

logger = logging.getLogger(__name__)


class HandlerError(Exception):
    def __init__(
        self,
        evento: CloudMessage[TEvento],
        handler: IMessageHandler[TEvent] | Callable[..., None],
        error: Exception,
    ):
        super().__init__(f"""
Error al Manejar Evento {evento.__class__.__name__}
    handler: {
            handler.__class__.__name__   # pyright: ignore[reportUnknownMemberType]
            if isinstance(handler, IMessageHandler)
            else handler.__name__ 
        }   
    evento: {evento.type}
    datos: {evento.model_dump_json(indent=2)}
    error: {error}
    stacktrace: {error.__traceback__}
        """)  # type: ignore  # noqa: E501


class BaseEventBus(IEventBus[TManager], MessageBus[TManager]):
    handlers: Dict[str, Dict[str, IMessageHandler[Any]]]
    wait_list: Dict[str, List[Callable[..., None]]]

    def initialize(self, env: Mapping[str, str]) -> None:
        self.handlers = {}
        self.wait_list = {}
        self.raise_error = strtobool(env.get(EVENT_BUS_RAISE_ERROR, "false"))
        super().initialize(env)

    def _get_key(self, obj: Type[TEvent] | IMessageHandler[TEvent]) -> str:
        if not isinstance(obj, IMessageHandler):
            return get_topic(obj)
        try:
            return get_topic(obj.__class__)
        except TopicError as e:
            raise HandlerAlreadyRegistered(
                f"Handler: {obj.__class__}, error: {e}"
            ) from e

    def subscribe(self, event_type: Type[TEvent], handler: IMessageHandler[TEvent]):
        self.verify()
        key_event = self._get_key(event_type)
        handlers = self.handlers.get(key_event, {})
        key_handler = self._get_key(handler)
        if key_handler in handlers:
            raise HandlerAlreadyRegistered(f"Event: {key_event}")
        handlers[key_handler] = handler
        self.handlers[key_event] = handlers

    def unsubscribe(self, event_type: Type[TEvent], *handlers: IMessageHandler[TEvent]):
        self.verify()
        key_event = self._get_key(event_type)
        if not handlers:
            if key_event in self.handlers:
                del self.handlers[key_event]
            return
        for handler in handlers:
            key_handler = self._get_key(handler)
            dict_handlers = self.handlers.get(key_event)
            if not dict_handlers:
                raise HandlerNotRegistered(f"Event: {key_event}")
            if key_handler not in dict_handlers:
                raise HandlerNotRegistered(f"Event: {key_event}")
            del dict_handlers[key_handler]

        if not list(self.handlers[key_event].values()):
            del self.handlers[key_event]

    def _wait_for(self, event_type: Type[TEvent], handler: Callable[[TEvent], None]):
        name = self._get_key(event_type)
        if name not in self.wait_list:
            self.wait_list[name] = []
        self.wait_list[name].append(handler)

    def _handle_wait_list(self, event: TEvento):
        event_type = type(event)
        key = self._get_key(event_type)
        wait_list = self.wait_list.get(key)
        while wait_list:
            if self.raise_error:
                handler = wait_list.pop()
                handler(event)
            else:
                try:
                    handler = wait_list.pop()
                    handler(event)
                except Exception as e:
                    raise HandlerError(event, handler, e) from e  # type: ignore

    @overload
    def wait_for_publish(
        self, event_type: Type[TEvent], handler: Callable[[TEvent], None]
    ) -> None: ...

    @overload
    def wait_for_publish(
        self, event_type: Type[TEvent]
    ) -> Callable[[Callable[[TEvent], None]], None]: ...

    def wait_for_publish(
        self, event_type: Type[TEvent], handler: Callable[[TEvent], None] | None = None
    ) -> Callable[[Callable[[TEvent], None]], None] | None:
        self.verify()
        if handler:
            return self._wait_for(event_type, handler)

        def decorator(func: Callable[[TEvent], None]):
            self._wait_for(event_type, func)

        return decorator

    def _get_handlers(self, message: CloudMessage[TEvento]) -> list[str]:
        key_event = self._get_key(type(message.payload))
        handlers = self.handlers.get(key_event, {})
        return list(handlers.keys())

    def _handle_message(self, message: CloudMessage[TEvento], handler: str) -> None:
        handlers = self.handlers.get(self._get_key(type(message.payload)))
        if not handlers or handler not in handlers:
            raise HandlerNotRegistered(f"Event: {handler}")
        try:
            handlers[handler].handle_message(message)
        except Exception as e:
            if self.raise_error:
                logger.exception(
                    "Error al Manejar Evento %s, con handler %s", message, handler
                )
                raise
            raise HandlerError(message, handlers[handler], e) from e

    def _publish_message(self, message: CloudMessage[TEvento]) -> None:
        try:
            self._handle_wait_list(message.payload)
        except HandlerError as e:
            logger.error(e)

    def process_events(self, *events: CloudMessage[TEvent]) -> None:
        return self._process_messages(*events)
