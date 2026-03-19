"""Public SQLAlchemy integration surface.

This module is the supported adapter-specific namespace for reusable
SQLAlchemy infrastructure helpers. The legacy
``hexagonal.adapters.drivens.repository.sqlalchemy`` path remains available for
backward compatibility, but new consumer imports should use this module.
"""

from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyDatastore,
    SQLAlchemyEntityRepositoryAdapter,
    SQLAlchemyInboxRepository,
    SQLAlchemyInfrastructure,
    SQLAlchemyOutboxRepository,
    SQLAlchemyPairInboxOutbox,
    SQLAlchemyRepositoryAdapter,
    SQLAlchemySearchRepositoryAdapter,
    SQLAlchemyUnitOfWork,
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

__all__ = [
    "SQLALCHEMY_DATABASE_URL",
    "SQLALCHEMY_ECHO",
    "SQLALCHEMY_MAX_OVERFLOW",
    "SQLALCHEMY_POOL_PRE_PING",
    "SQLALCHEMY_POOL_RECYCLE",
    "SQLALCHEMY_POOL_SIZE",
    "SQLALCHEMY_POOL_TIMEOUT",
    "SQLAlchemyConnectionContextManager",
    "SQLAlchemyDatastore",
    "SQLAlchemyEntityRepositoryAdapter",
    "SQLAlchemyInboxRepository",
    "SQLAlchemyInfrastructure",
    "SQLAlchemyOutboxRepository",
    "SQLAlchemyPairInboxOutbox",
    "SQLAlchemyRepositoryAdapter",
    "SQLAlchemySearchRepositoryAdapter",
    "SQLAlchemyUnitOfWork",
]
