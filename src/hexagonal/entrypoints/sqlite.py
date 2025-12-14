from typing import Mapping, Optional

from eventsourcing.compressor import ZlibCompressor
from eventsourcing.utils import strtobool

from hexagonal.adapters.drivens.mappers import MessageMapper, OrjsonTranscoder
from hexagonal.adapters.drivens.repository.sqlite import (
    SQLiteConnectionContextManager,
    SQLiteDatastore,
    SQLiteInfrastructure,
    SQLitePairInboxOutbox,
)
from hexagonal.entrypoints import AppEntrypoint, Entrypoint


class SQLiteInfrastructureEntrypoint(Entrypoint[SQLiteInfrastructure]):
    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        env = cls.construct_env(env)
        db_path = env.get("SQLITE_DB_PATH")
        if db_path is None:
            raise ValueError("Database configuration is missing")
        check_same_thread = strtobool(env.get("SQLITE_CHECK_SAME_THREAD", "True"))
        datastore = SQLiteDatastore(
            db_path,
            check_same_thread=check_same_thread,
        )
        mapper = MessageMapper(
            transcoder=OrjsonTranscoder(), compressor=ZlibCompressor()
        )
        infrastructure = SQLiteInfrastructure(mapper, datastore)
        infrastructure.initialize(env)
        return infrastructure


class SQLiteOutboxEntrypoint(Entrypoint[SQLitePairInboxOutbox]):
    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        env = cls.construct_env(env)
        infrastructure = SQLiteInfrastructureEntrypoint.get(env)
        pair = SQLitePairInboxOutbox(
            infrastructure.mapper, infrastructure.connection_manager
        )
        pair.initialize(env)
        return pair


class SQLiteAppEntrypoint(AppEntrypoint[SQLiteConnectionContextManager]):
    OUTBOX = SQLiteOutboxEntrypoint
