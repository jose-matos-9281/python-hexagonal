"""SQLAlchemy infrastructure grouping."""

from hexagonal.adapters.drivens.mappers import MessageMapper
from hexagonal.application import ComposableInfrastructure

from .datastore import SQLAlchemyConnectionContextManager, SQLAlchemyDatastore


class SQLAlchemyInfrastructure(ComposableInfrastructure):
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
        self._datastore = datastore
        self._mapper = mapper
        self._connection_manager = SQLAlchemyConnectionContextManager(datastore)
        super().__init__(self._connection_manager)

    @property
    def connection_manager(self) -> SQLAlchemyConnectionContextManager:
        """Get the connection context manager."""
        return self._connection_manager

    @property
    def mapper(self) -> MessageMapper:
        """Get the message mapper."""
        return self._mapper
