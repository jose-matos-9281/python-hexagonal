"""SQLAlchemy Unit of Work implementation."""

from typing import Optional

from hexagonal.adapters.drivens.repository.base import BaseUnitOfWork
from hexagonal.ports.drivens.repository import IBaseRepository

from .datastore import SQLAlchemyConnectionContextManager


class SQLAlchemyUnitOfWork(BaseUnitOfWork[SQLAlchemyConnectionContextManager]):
    """SQLAlchemy implementation of the Unit of Work pattern.

    Coordinates transaction management across multiple repositories.
    Uses SQLAlchemy Connection's commit/rollback for transaction control.

    The UoW ensures all repository operations within its context share
    the same database connection and transaction, providing atomicity
    across multiple aggregate modifications.
    """

    def __init__(
        self,
        *repositories: IBaseRepository[SQLAlchemyConnectionContextManager],
        connection_manager: Optional[SQLAlchemyConnectionContextManager] = None,
    ):
        """Initialize the Unit of Work.

        Args:
            repositories: Variable number of repositories to attach
            connection_manager: Optional connection manager. If not provided,
                              a new one will be created (requires initialize())
        """
        if connection_manager is None:
            connection_manager = SQLAlchemyConnectionContextManager()
        super().__init__(*repositories, connection_manager=connection_manager)

    def commit(self) -> None:
        """Commit the current transaction.

        Persists all changes made by attached repositories.

        Raises:
            RuntimeError: If the UoW is not in an active transaction
        """
        self.verify()
        # SQLAlchemy Connection.commit() commits the current transaction
        self.connection_manager.current_connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction.

        Reverts all changes made by attached repositories.

        Raises:
            RuntimeError: If the UoW is not in an active transaction
        """
        self.verify()
        # SQLAlchemy Connection.rollback() rolls back the current transaction
        self.connection_manager.current_connection.rollback()
