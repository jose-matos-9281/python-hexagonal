"""SQLAlchemy infrastructure grouping."""

import threading
from typing import Callable, Generic, Mapping, TypeVar

from hexagonal.adapters.drivens.mappers import MessageMapper
from hexagonal.application import Infrastructure
from hexagonal.ports.drivens.repository import TResult

from .datastore import SQLAlchemyConnectionContextManager, SQLAlchemyDatastore

TWriteScope = TypeVar("TWriteScope")
TReadScope = TypeVar("TReadScope")


class SQLAlchemyScopeRunner(Generic[TWriteScope, TReadScope]):
    def __init__(
        self,
        create_write_scope: Callable[[], TWriteScope],
        create_read_scope: Callable[[], TReadScope],
    ):
        self._create_write_scope = create_write_scope
        self._create_read_scope = create_read_scope
        self._local = threading.local()

    def run_in_write_scope(self, work: Callable[[TWriteScope], TResult]) -> TResult:
        stack: list[TWriteScope] | None = getattr(
            self._local, "write_scope_stack", None
        )
        if stack is None:
            stack = []
            self._local.write_scope_stack = stack

        if stack:
            return work(stack[-1])

        scope = self._create_write_scope()
        stack.append(scope)
        try:
            return work(scope)
        finally:
            stack.pop()

    def run_in_read_scope(self, work: Callable[[TReadScope], TResult]) -> TResult:
        return work(self._create_read_scope())

    @property
    def current_write_scope(self) -> TWriteScope | None:
        stack = getattr(self._local, "write_scope_stack", None)
        if not stack:
            return None
        return stack[-1]


class SQLAlchemyInfrastructure(Infrastructure):
    """Groups SQLAlchemy connection manager and mapper for dependency injection.

    Provides a convenient way to initialize and access the core
    SQLAlchemy infrastructure components needed by repositories.
    """

    def __init__(
        self,
        mapper: MessageMapper,
        datastore: SQLAlchemyDatastore | None = None,
    ):
        """Initialize SQLAlchemy infrastructure.

        Args:
            mapper: Message mapper for serialization/deserialization
            datastore: Optional SQLAlchemyDatastore instance.
                      If not provided, connection_manager.initialize() must be called.
        """
        super().__init__()
        self._datastore = datastore
        self._mapper = mapper
        self._env: Mapping[str, str] = {}
        self._initialized = datastore is not None

    def initialize(self, env: Mapping[str, str]) -> None:
        self._env = dict(env)
        self._initialized = True

    @property
    def datastore(self) -> SQLAlchemyDatastore:
        if self._datastore is None:
            raise RuntimeError("Datastore not initialized. Call initialize() first.")
        return self._datastore

    @property
    def connection_manager(self) -> SQLAlchemyConnectionContextManager:
        return self.create_connection_manager()

    def create_connection_manager(self) -> SQLAlchemyConnectionContextManager:
        return SQLAlchemyConnectionContextManager(self.datastore)

    @property
    def mapper(self) -> MessageMapper:
        """Get the message mapper."""
        return self._mapper
