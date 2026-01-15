"""SQLAlchemy adapters for the repository pattern.

This module provides SQLAlchemy-based implementations of the repository,
outbox, inbox, and unit of work patterns. Supports multiple database
backends (PostgreSQL, MySQL, SQLite) through SQLAlchemy's abstraction layer.
"""

from .datastore import SQLAlchemyConnectionContextManager, SQLAlchemyDatastore
from .infrastructure import SQLAlchemyInfrastructure
from .outbox import (
    SQLAlchemyInboxRepository,
    SQLAlchemyOutboxRepository,
    SQLAlchemyPairInboxOutbox,
)
from .repository import SQLAlchemyRepositoryAdapter
from .unit_of_work import SQLAlchemyUnitOfWork

__all__ = [
    "SQLAlchemyConnectionContextManager",
    "SQLAlchemyDatastore",
    "SQLAlchemyRepositoryAdapter",
    "SQLAlchemyUnitOfWork",
    "SQLAlchemyOutboxRepository",
    "SQLAlchemyInboxRepository",
    "SQLAlchemyInfrastructure",
    "SQLAlchemyPairInboxOutbox",
]
