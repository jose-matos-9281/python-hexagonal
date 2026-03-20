from typing import Any, Mapping, Type

from eventsourcing.utils import get_topic

from hexagonal.domain import (
    CloudMessage,
    HandlerAlreadyRegistered,
    HandlerNotRegistered,
    TCommand,
)
from hexagonal.ports.drivens import ICommandBus, IMessageHandler, TManager

from .message_bus import MessageBus


class BaseCommandBus(ICommandBus[TManager], MessageBus[TManager]):
    _handlers: dict[str, IMessageHandler[Any]]

    def initialize(self, env: Mapping[str, str]) -> None:
        self.__class__._handlers = {}
        super().initialize(env)

    def _get_name(self, command_type: Type[TCommand]) -> str:
        return get_topic(command_type)

    def _get_handlers(self, message: CloudMessage[TCommand]) -> list[str]:
        return [self._get_name(message.payload.__class__)]

    def _handle_message(self, message: CloudMessage[TCommand], handler: str) -> None:
        f_handler = self._handlers.get(handler)
        if f_handler:
            f_handler.handle_message(message)
        else:
            raise HandlerNotRegistered(f"Command: {handler}")

    def register_handler(
        self, command_type: Type[TCommand], handler: IMessageHandler[TCommand]
    ) -> None:
        self.verify()
        name = self._get_name(command_type)
        if name in self._handlers:
            raise HandlerAlreadyRegistered(f"Command: {name}")
        self._handlers[name] = handler

    def unregister_handler(self, command_type: Type[TCommand]) -> None:
        self.verify()
        name = self._get_name(command_type)
        if name in self._handlers:
            del self._handlers[name]
        else:
            raise HandlerNotRegistered(f"Command: {name}")

    def dispatch(
        self,
        command: CloudMessage[TCommand],
        *,
        to_outbox: bool = False,
    ) -> None:
        self.verify()
        if to_outbox:
            self.save_to_outbox(command)
        else:
            self.process_command(command)

    def process_command(self, command: CloudMessage[TCommand]) -> None:
        self._process_messages(command)
