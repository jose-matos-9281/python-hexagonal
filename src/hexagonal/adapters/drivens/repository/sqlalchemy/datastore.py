"""SQLAlchemy datastore and connection context manager."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Optional

from eventsourcing.utils import strtobool
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.pool import QueuePool, StaticPool

from hexagonal.ports.drivens.repository import IConnectionManager

from .env_vars import (
    SQLALCHEMY_DATABASE_URL,
    SQLALCHEMY_ECHO,
    SQLALCHEMY_MAX_OVERFLOW,
    SQLALCHEMY_POOL_PRE_PING,
    SQLALCHEMY_POOL_RECYCLE,
    SQLALCHEMY_POOL_SIZE,
    SQLALCHEMY_POOL_TIMEOUT,
)


class SQLAlchemyDatastore:
    """Core SQLAlchemy engine and connection management.

    Wraps SQLAlchemy Engine with connection pooling configuration.
    Provides context managers for connection and transaction handling.
    """

    def __init__(
        self,
        database_url: str,
        *,
        echo: bool = False,
        pool_size: int = 5,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        max_overflow: int = 10,
    ):
        """Initialize SQLAlchemy datastore.

        Args:
            database_url: SQLAlchemy database URL (e.g., postgresql://user:pass@host/db)
            echo: Enable SQL statement logging
            pool_size: Connection pool size (ignored for SQLite)
            pool_timeout: Connection pool timeout in seconds
            pool_recycle: Connection recycle time in seconds
            pool_pre_ping: Pre-ping connections before use
            max_overflow: Maximum overflow connections (ignored for SQLite)
        """
        self._database_url = database_url

        # SQLite uses StaticPool for single connection (avoids database lock issues)
        # Other databases use QueuePool with configurable settings
        is_sqlite = database_url.startswith("sqlite")

        pool_class = StaticPool if is_sqlite else QueuePool
        pool_kwargs: dict[Any, Any] = {}

        if is_sqlite:
            # For SQLite with StaticPool, we need connect_args
            pool_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            pool_kwargs.update(
                {
                    "pool_size": pool_size,
                    "pool_timeout": pool_timeout,
                    "pool_recycle": pool_recycle,
                    "pool_pre_ping": pool_pre_ping,
                    "max_overflow": max_overflow,
                }
            )

        self._engine: Engine = create_engine(
            database_url,
            echo=echo,
            poolclass=pool_class,
            **pool_kwargs,
        )

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine."""
        return self._engine

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return self._database_url

    @contextmanager
    def get_connection(self) -> Iterator[Connection]:
        """Get a database connection from the pool.

        Yields:
            SQLAlchemy Connection object

        The connection is returned to the pool when the context exits.
        """
        with self._engine.connect() as connection:
            # Enable foreign key support for SQLite
            if self._database_url.startswith("sqlite"):
                connection.execute(text("PRAGMA foreign_keys = ON"))
            yield connection

    @contextmanager
    def transaction(self, commit: bool = False) -> Iterator[Connection]:
        """Get a connection with transaction management.

        Args:
            commit: If True, commit the transaction on success

        Yields:
            SQLAlchemy Connection object within a transaction

        Raises:
            RuntimeError: If the transaction fails (wraps original exception)
        """
        with self.get_connection() as connection:
            trans = connection.begin()
            try:
                yield connection
                if commit:
                    trans.commit()
                else:
                    trans.rollback()
            except Exception as exc:
                trans.rollback()
                raise RuntimeError("Transaction failed") from exc

    def dispose(self) -> None:
        """Dispose of the engine and all connections."""
        self._engine.dispose()


class SQLAlchemyConnectionContextManager(IConnectionManager):
    """Connection context manager implementing IConnectionManager interface.

    Manages SQLAlchemy connection lifecycle for repositories.
    Maintains a current connection reference for transaction coordination.
    """

    def __init__(self, datastore: Optional[SQLAlchemyDatastore] = None):
        """Initialize connection context manager.

        Args:
            datastore: Optional SQLAlchemyDatastore instance.
                      If not provided, must call initialize() before use.
        """
        self._datastore = datastore
        self._current_connection: Optional[Connection] = None
        self._connection_ctx: Optional[Any] = None
        self._initialized = datastore is not None

    @property
    def initialized(self) -> bool:
        """Check if the connection manager is initialized."""
        return self._initialized

    @property
    def datastore(self) -> SQLAlchemyDatastore:
        """Get the underlying datastore.

        Raises:
            RuntimeError: If datastore is not initialized
        """
        if self._datastore is None:
            raise RuntimeError("Datastore not initialized. Call initialize() first.")
        return self._datastore

    def initialize(self, env: Mapping[str, str]) -> None:
        """Initialize the datastore from environment variables.

        Args:
            env: Environment variables mapping

        Environment variables:
            SQLALCHEMY_DATABASE_URL: Database connection URL (required)
            SQLALCHEMY_ECHO: Enable SQL logging (default: False)
            SQLALCHEMY_POOL_SIZE: Pool size (default: 5)
            SQLALCHEMY_POOL_TIMEOUT: Pool timeout (default: 30)
            SQLALCHEMY_POOL_RECYCLE: Pool recycle time (default: 3600)
            SQLALCHEMY_POOL_PRE_PING: Pre-ping connections (default: True)
            SQLALCHEMY_MAX_OVERFLOW: Max overflow (default: 10)
        """
        if self._datastore is not None:
            self._initialized = True
            return

        database_url = env.get(SQLALCHEMY_DATABASE_URL)
        if database_url is None:
            raise ValueError(
                f"Database configuration is missing. Set {SQLALCHEMY_DATABASE_URL}."
            )

        echo = strtobool(env.get(SQLALCHEMY_ECHO, "False"))
        pool_size = int(env.get(SQLALCHEMY_POOL_SIZE, "5"))
        pool_timeout = int(env.get(SQLALCHEMY_POOL_TIMEOUT, "30"))
        pool_recycle = int(env.get(SQLALCHEMY_POOL_RECYCLE, "3600"))
        pool_pre_ping = strtobool(env.get(SQLALCHEMY_POOL_PRE_PING, "True"))
        max_overflow = int(env.get(SQLALCHEMY_MAX_OVERFLOW, "10"))

        self._datastore = SQLAlchemyDatastore(
            database_url,
            echo=bool(echo),
            pool_size=pool_size,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=bool(pool_pre_ping),
            max_overflow=max_overflow,
        )
        self._initialized = True

    def start_connection(self):
        """Start a new connection context.

        Returns:
            The connection context manager (already entered)

        This manually enters the connection context and sets it as current.
        Call the returned context's __exit__ to clean up.
        """
        self._connection_ctx = self.datastore.get_connection()
        self._current_connection = self._connection_ctx.__enter__()
        return self._connection_ctx

    @property
    def current_connection(self) -> Connection:
        """Get the current active connection.

        Returns:
            The current SQLAlchemy Connection

        Note:
            If no connection exists or it's closed, a new one will be created.
        #"""
        if self._current_connection is None or self._current_connection.closed:
            self._connection_ctx = self.datastore.get_connection()
            self._current_connection = self._connection_ctx.__enter__()
        if self._current_connection is None:
            raise RuntimeError("Failed to establish a database connection.")
        return self._current_connection

    @current_connection.setter
    def current_connection(self, connection: Optional[Connection]) -> None:
        """Set the current connection, cleaning up any existing one.

        Args:
            connection: The new connection or None to clear
        """
        if self._connection_ctx is not None:
            try:
                self._connection_ctx.__exit__(None, None, None)
            except Exception:
                pass  # Ignore errors during cleanup
            self._connection_ctx = None
        self._current_connection = connection

    @contextmanager
    def cursor(self, commit: bool = True) -> Iterator[Connection]:
        """Get a connection for executing statements.

        This is provided for compatibility with the SQLite interface.
        In SQLAlchemy, we use the connection directly instead of a cursor.

        Handles closed connections by re-establishing.

        Args:
            commit: Whether to commit after the context exits (default: True)

        Yields:
            Current connection for executing statements
        """
        try:
            # Check if connection is usable
            conn = self.current_connection
            if conn.closed:
                self._current_connection = None
                conn = self.current_connection
            yield conn
            if commit:
                conn.commit()
        except Exception:
            # Reset connection on error
            self._current_connection = None
            raise
