from hexagonal.adapters.drivens.mappers import MessageMapper
from hexagonal.application import ComposableInfrastructure

from .datastore import SQLiteConnectionContextManager, SQLiteDatastore


class SQLiteInfrastructure(ComposableInfrastructure):
    def __init__(self, mapper: MessageMapper, datastore: SQLiteDatastore | None = None):
        self._datastore = datastore
        self._mapper = mapper
        self._connection_manager = SQLiteConnectionContextManager(datastore)
        super().__init__(self._connection_manager)

    @property
    def connection_manager(self) -> SQLiteConnectionContextManager:
        return self._connection_manager

    @property
    def mapper(self) -> MessageMapper:
        return self._mapper
