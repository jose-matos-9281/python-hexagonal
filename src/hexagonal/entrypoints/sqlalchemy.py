"""SQLAlchemy entrypoints for infrastructure bootstrapping."""

from typing import Mapping, Optional

from eventsourcing.compressor import ZlibCompressor
from eventsourcing.utils import strtobool

from hexagonal.adapters.drivens.mappers import MessageMapper, OrjsonTranscoder
from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyDatastore,
    SQLAlchemyInfrastructure,
    SQLAlchemyPairInboxOutbox,
)
from hexagonal.adapters.drivens.repository.sqlalchemy.env_vars import (
    SQLALCHEMY_DATABASE_URL,
    SQLALCHEMY_ECHO,
    SQLALCHEMY_MAX_OVERFLOW,
    SQLALCHEMY_POOL_PRE_PING,
    SQLALCHEMY_POOL_RECYCLE,
    SQLALCHEMY_POOL_SIZE,
    SQLALCHEMY_POOL_TIMEOUT,
)
from hexagonal.entrypoints import AppEntrypoint, Entrypoint

# Cache for infrastructure instances to ensure same database URL reuses the same
# datastore and connection manager. Key is the database URL.
_infrastructure_cache: dict[str, SQLAlchemyInfrastructure] = {}


def clear_infrastructure_cache() -> None:
    """Clear the infrastructure cache.

    Useful for testing when you need to reset the cached infrastructure.
    """
    _infrastructure_cache.clear()


class SQLAlchemyInfrastructureEntrypoint(Entrypoint[SQLAlchemyInfrastructure]):
    """Entrypoint for bootstrapping SQLAlchemy infrastructure from environment.

    Reads configuration from environment variables and creates the
    SQLAlchemy datastore, mapper, and infrastructure components.

    Environment variables:
        SQLALCHEMY_DATABASE_URL: Database connection URL (required)
        SQLALCHEMY_ECHO: Enable SQL logging (default: False)
        SQLALCHEMY_POOL_SIZE: Connection pool size (default: 5)
        SQLALCHEMY_POOL_TIMEOUT: Pool timeout in seconds (default: 30)
        SQLALCHEMY_POOL_RECYCLE: Pool recycle time in seconds (default: 3600)
        SQLALCHEMY_POOL_PRE_PING: Pre-ping connections (default: True)
        SQLALCHEMY_MAX_OVERFLOW: Max overflow connections (default: 10)
    """

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None) -> SQLAlchemyInfrastructure:
        """Create and initialize SQLAlchemy infrastructure.

        Uses a cache to ensure the same database URL returns the same
        infrastructure instance. This is critical for SQLite where multiple
        connections cause database locking issues.

        Args:
            env: Optional environment variables mapping.
                 Falls back to os.environ if not provided.

        Returns:
            Initialized SQLAlchemyInfrastructure instance

        Raises:
            ValueError: If SQLALCHEMY_DATABASE_URL is not set
        """
        env = cls.construct_env(env)

        database_url = env.get(SQLALCHEMY_DATABASE_URL)
        if database_url is None:
            raise ValueError(
                f"Database configuration is missing. Set {SQLALCHEMY_DATABASE_URL}."
            )

        # Return cached infrastructure if available
        if database_url in _infrastructure_cache:
            return _infrastructure_cache[database_url]

        # Parse optional configuration
        echo = bool(strtobool(env.get(SQLALCHEMY_ECHO, "False")))
        pool_size = int(env.get(SQLALCHEMY_POOL_SIZE, "5"))
        pool_timeout = int(env.get(SQLALCHEMY_POOL_TIMEOUT, "30"))
        pool_recycle = int(env.get(SQLALCHEMY_POOL_RECYCLE, "3600"))
        pool_pre_ping = bool(strtobool(env.get(SQLALCHEMY_POOL_PRE_PING, "True")))
        max_overflow = int(env.get(SQLALCHEMY_MAX_OVERFLOW, "10"))

        datastore = SQLAlchemyDatastore(
            database_url,
            echo=echo,
            pool_size=pool_size,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            max_overflow=max_overflow,
        )

        mapper = MessageMapper(
            transcoder=OrjsonTranscoder(), compressor=ZlibCompressor()
        )

        infrastructure = SQLAlchemyInfrastructure(mapper, datastore)
        infrastructure.initialize(env)

        # Cache the infrastructure for reuse
        _infrastructure_cache[database_url] = infrastructure

        return infrastructure


class SQLAlchemyOutboxEntrypoint(Entrypoint[SQLAlchemyPairInboxOutbox]):
    """Entrypoint for bootstrapping SQLAlchemy inbox/outbox pair.

    Creates the infrastructure and then the inbox/outbox repositories.
    """

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None) -> SQLAlchemyPairInboxOutbox:
        """Create and initialize SQLAlchemy inbox/outbox pair.

        Args:
            env: Optional environment variables mapping.
                 Falls back to os.environ if not provided.

        Returns:
            Initialized SQLAlchemyPairInboxOutbox instance
        """
        env = cls.construct_env(env)
        infrastructure = SQLAlchemyInfrastructureEntrypoint.get(env)
        pair = SQLAlchemyPairInboxOutbox(
            infrastructure.mapper, infrastructure.connection_manager
        )
        pair.initialize(env)
        return pair


class SQLAlchemyAppEntrypoint(AppEntrypoint[SQLAlchemyConnectionContextManager]):
    """Base entrypoint for SQLAlchemy-based applications.

    Provides the OUTBOX configuration for application entrypoints.
    """

    OUTBOX = SQLAlchemyOutboxEntrypoint
