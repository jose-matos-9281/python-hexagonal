import logging
from typing import Callable, Generic, Protocol, TypeVar, Union

logger = logging.getLogger(__name__)

TWriteScope = TypeVar("TWriteScope")
TReadScope = TypeVar("TReadScope")
TWriteScope_contra = TypeVar("TWriteScope_contra", contravariant=True)
TResult = TypeVar("TResult")
TReadScope_co = TypeVar("TReadScope_co", covariant=True)
TWriteScope_co = TypeVar("TWriteScope_co", covariant=True)

TScope = Union[TWriteScope, TReadScope]


class IWriteScopeFactory(Protocol, Generic[TWriteScope_co]):
    def create_write_scope(self) -> TWriteScope_co: ...


class IReadScopeFactory(Protocol, Generic[TReadScope_co]):
    def create_read_scope(self) -> TReadScope_co: ...


class IWriteScopeRunner(Protocol, Generic[TWriteScope_co]):
    @property
    def current_write_scope(self) -> TWriteScope_co | None: ...

    def run_in_write_scope(
        self, work: Callable[[TWriteScope_co], TResult]
    ) -> TResult: ...


class IReadScopeRunner(Protocol, Generic[TReadScope_co]):
    def run_in_read_scope(
        self, work: Callable[[TReadScope_co], TResult]
    ) -> TResult: ...
