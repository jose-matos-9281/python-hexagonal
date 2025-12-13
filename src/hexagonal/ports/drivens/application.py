from abc import ABC, abstractmethod
from typing import Generic, Iterable

from hexagonal.domain import (
    CloudMessage,
    QueryResults,
    TEvento,
    TMessagePayloadType,
    TQuery,
    TView,
)

from .repository import ISearchRepository, TManager


class IUseCase(ABC):
    @abstractmethod
    def execute(self) -> Iterable[TEvento]: ...


class IMessageHandler(ABC, Generic[TMessagePayloadType]):
    @abstractmethod
    def handle_message(self, message: CloudMessage[TMessagePayloadType]) -> None: ...

    @abstractmethod
    def get_use_case(self, message: TMessagePayloadType) -> IUseCase: ...


class IQueryHandler(ABC, Generic[TManager, TQuery, TView]):
    @property
    @abstractmethod
    def repository(self) -> ISearchRepository[TManager, TQuery, TView]: ...

    @abstractmethod
    def get(self, query: TQuery) -> QueryResults[TView]: ...
