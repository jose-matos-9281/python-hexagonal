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
        evento: CloudMessage[TEvento] | TEvento,
        handler: IMessageHandler[TEvent] | Callable[..., None],
        error: Exception,
    ) -> None:
        handler_name = (
            handler.__class__.__name__
            if isinstance(handler, IMessageHandler)
            else handler.__name__
        )
        event_name = (
            evento.__class__.__name__
            if not isinstance(evento, CloudMessage)
            else evento.payload.__class__.__name__
        )
        event_topic = (
            evento.TOPIC if not isinstance(evento, CloudMessage) else evento.type
        )
        event_dump = (
            evento.model_dump_json(indent=2)
            if not isinstance(evento, CloudMessage)
            else evento.model_dump_json(indent=2)
        )
        super().__init__(f"""
Error al Manejar Evento {event_name}
    handler: {handler_name}
    evento: {event_topic}
    datos: {event_dump}
    error: {error}
    stacktrace: {error.__traceback__}
        """)


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
        handler_key = getattr(obj, "handler_key", None)
        if isinstance(handler_key, str):
            return handler_key
        try:
            return get_topic(obj.__class__)
        except TopicError as e:
            raise HandlerAlreadyRegistered(
                f"Handler: {obj.__class__}, error: {e}"
            ) from e

    def subscribe(
        self, event_type: Type[TEvent], handler: IMessageHandler[TEvent]
    ) -> None:
        self.verify()
        key_event = self._get_key(event_type)
        handlers = self.handlers.get(key_event, {})
        key_handler = self._get_key(handler)
        if key_handler in handlers:
            raise HandlerAlreadyRegistered(f"Event: {key_event}")
        handlers[key_handler] = handler
        self.handlers[key_event] = handlers

    def unsubscribe(
        self, event_type: Type[TEvent], *handlers: IMessageHandler[TEvent]
    ) -> None:
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

    def _wait_for(
        self, event_type: Type[TEvent], handler: Callable[[TEvent], None]
    ) -> None:
        name = self._get_key(event_type)
        if name not in self.wait_list:
            self.wait_list[name] = []
        self.wait_list[name].append(handler)
        logger.debug(
            "    [DEBUG _wait_for] Added handler to wait_list[%s], now has %s handlers",
            name,
            len(self.wait_list[name]),
        )

    def _handle_wait_list(self, event: TEvento) -> None:
        event_type = type(event)
        key = self._get_key(event_type)
        logger.debug("    [DEBUG _handle_wait_list] Publishing event type=%s", key)
        wait_list = self.wait_list.get(key)
        if wait_list:
            logger.debug(
                "    [DEBUG _handle_wait_list] Found %s handlers", len(wait_list)
            )
        else:
            logger.debug("    [DEBUG _handle_wait_list] No handlers registered!")
        while wait_list:
            if self.raise_error:
                immediate_handler = wait_list.pop()
                immediate_handler(event)
            else:
                queued_handler: Callable[[TEvento], None] | None = None
                try:
                    queued_handler = wait_list.pop()
                    queued_handler(event)
                except Exception as e:
                    if queued_handler is None:
                        raise
                    raise HandlerError(event, queued_handler, e) from e

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
            self._wait_for(event_type, handler)
            return None

        def decorator(func: Callable[[TEvent], None]) -> None:
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
        self._process_messages(*events)
