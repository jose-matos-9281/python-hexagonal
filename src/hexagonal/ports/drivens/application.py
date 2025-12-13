from abc import ABC, abstractmethod
from typing import Generic

from hexagonal.domain import (
    CloudMessage,
    QueryResults,
    TMessagePayloadType,
    TQuery,
    TView,
    UseCase,
)

from .repository import ISearchRepository, TManager


class MessageHandler(ABC, Generic[TMessagePayloadType]):
    @abstractmethod
    def handle_message(self, message: CloudMessage[TMessagePayloadType]) -> None: ...

    @abstractmethod
    def get_use_case(self, message: TMessagePayloadType) -> UseCase: ...


class QueryHandler(ABC, Generic[TManager, TQuery, TView]):
    @property
    @abstractmethod
    def repository(self) -> ISearchRepository[TManager, TQuery, TView]: ...

    @abstractmethod
    def get(self, query: TQuery) -> QueryResults[TView]: ...
