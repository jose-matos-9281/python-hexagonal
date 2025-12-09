from abc import ABC, abstractmethod
from typing import Generic, Iterable

from hexagonal.domain.base import (
    CloudMessage,
    QueryResults,
    TEvento,
    TMessagePayloadType,
    TQuery,
    TView,
)


class UseCase(ABC):
    @abstractmethod
    def execute(self) -> Iterable[TEvento]: ...


class MessageHandler(ABC, Generic[TMessagePayloadType]):
    @abstractmethod
    def handle_message(self, message: CloudMessage[TMessagePayloadType]) -> None: ...

    @abstractmethod
    def get_use_case(self, message: TMessagePayloadType) -> UseCase: ...


class QueryHandler(ABC, Generic[TQuery, TView]):
    @abstractmethod
    def get(self, query: TQuery) -> QueryResults[TView]: ...
