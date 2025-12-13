"""SQLite datastore implementation for the repository pattern."""

import sqlite3
from contextlib import contextmanager
from typing import Callable, Iterator, Literal, Mapping, Optional, TypeVar

from eventsourcing.utils import strtobool

from hexagonal.application import Infrastructure
from hexagonal.ports.drivens import IConnectionManager

from .env_vars import SQLITE_CHECK_SAME_THREAD, SQLITE_DB_PATH

# Type variable for the connection type
T = TypeVar("T", bound=sqlite3.Connection)

# Type alias for SQLite isolation levels


class SQLiteDatastore(Infrastructure):
    """SQLite datastore adapter that provides connection and transaction management."""

    def __init__(
        self,
        database: str,
        *,
        timeout: float = 5.0,
        detect_types: int = 0,
        isolation_level: Optional[Literal["DEFERRED", "IMMEDIATE", "EXCLUSIVE"]] = None,
        check_same_thread: bool = True,
        factory: Optional[Callable[..., sqlite3.Connection]] = None,
        cached_statements: int = 128,
        uri: bool = False,
        autocommit: bool = False,
    ):
        """Initialize SQLite datastore.

        Args:
            database: Path to the SQLite database file
            timeout: How many seconds the connection should wait
            before raising an exception
            detect_types: Control the type detection
            isolation_level: See sqlite3.Connection.isolation_level
            check_same_thread: If True, only the creating thread may use the connection
            factory: Custom connection factory
            (must be a callable that returns a Connection)
            cached_statements: Number of statements to cache
            uri: If True, database is interpreted as a URI
            autocommit: If True, the connection will be in autocommit mode
        """
        self.database = database
        self.timeout = timeout
        self.detect_types = detect_types
        self.isolation_level = isolation_level
        self.check_same_thread = check_same_thread
        self.factory = factory
        self.cached_statements = cached_statements
        self.uri = uri
        self.autocommit = autocommit
        self._connection: Optional[sqlite3.Connection] = None

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection from the pool.

        Yields:
            A database connection that will be automatically
            closed when the context exits

        Example:
            with datastore.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
        """
        conn = sqlite3.connect(
            database=self.database,
            timeout=self.timeout,
            detect_types=self.detect_types,
            check_same_thread=self.check_same_thread,
            cached_statements=self.cached_statements,
            uri=self.uri,
        )
        try:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.DatabaseError as e:
            raise Exception(f"SQLite DatabaseError: {e}") from e
        except sqlite3.InterfaceError as e:
            raise Exception(f"SQLite InterfaceError: {e}") from e
        # except Exception as e:
        #     raise Exception(f"SQLite Unknown error: {e}") from e
        finally:
            conn.close()

    @contextmanager
    def transaction(self, commit: bool = False) -> Iterator[sqlite3.Cursor]:
        """Execute a transaction on the database.

        Args:
            commit: If True, commit the transaction after the block completes.
                   If False, rollback the transaction if an exception occurs.

        Yields:
            A database cursor for executing SQL statements.

        Example:
            with datastore.transaction(commit=True) as cursor:
                cursor.execute('INSERT INTO table VALUES (?)', (value,))
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as exc:
                conn.rollback()
                raise RuntimeError("Transaction failed") from exc
            finally:
                cursor.close()

    def close(self) -> None:
        """Close any open connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        self._connection = self.get_connection().__enter__()
        self._connection.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self.close()

    def __del__(self):
        self.close()


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row, strict=False)}


class SQLiteConnectionContextManager(IConnectionManager, Infrastructure):
    def __init__(self, datastore: SQLiteDatastore | None = None):
        self._current_connection: sqlite3.Connection | None = None
        self._setted_datastore: bool = datastore is not None
        if datastore is not None:
            self._datastore = datastore
        super().__init__()

    def initialize(self, env: Mapping[str, str]) -> None:
        if self._setted_datastore:
            return super().initialize(env)
        db_path = env.get(SQLITE_DB_PATH, ":memory:")
        check_same_thread = strtobool(env.get(SQLITE_CHECK_SAME_THREAD, "True"))
        self._datastore = SQLiteDatastore(
            database=db_path,
            check_same_thread=check_same_thread,
        )
        super().initialize(env)

    @property
    def datastore(self) -> SQLiteDatastore:
        self.verify()
        return self._datastore

    def start_connection(self):
        self._ctx_con = self.datastore.get_connection()
        self._current_connection = self._ctx_con.__enter__()
        return self._ctx_con

    @property
    def current_connection(self) -> sqlite3.Connection:
        if self._current_connection is None:
            self._ctx_con = self.datastore.get_connection()
            self._current_connection = self._ctx_con.__enter__()
        return self._current_connection

    @current_connection.setter
    def current_connection(self, connection: sqlite3.Connection) -> None:
        if getattr(self, "_ctx_con", None):
            self._ctx_con.__exit__(None, None, None)
        self._current_connection = connection

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        try:
            cursor = self.current_connection.cursor()
        except sqlite3.ProgrammingError:
            self._current_connection = None
            cursor = self.current_connection.cursor()
        yield cursor
        cursor.close()
