from typing import Optional

from hexagonal.adapters.drivens.repository.base import BaseUnitOfWork
from hexagonal.ports.drivens.repository import IBaseRepository

from .datastore import SQLiteConnectionContextManager


class SQLiteUnitOfWork(BaseUnitOfWork[SQLiteConnectionContextManager]):
    def __init__(
        self,
        *repositories: IBaseRepository[SQLiteConnectionContextManager],
        connection_manager: Optional[SQLiteConnectionContextManager] = None,
    ):
        if connection_manager is None:
            connection_manager = SQLiteConnectionContextManager()
        super().__init__(*repositories, connection_manager=connection_manager)

    def commit(self) -> None:
        self.verify()
        return self.connection_manager.current_connection.commit()

    def rollback(self) -> None:
        self.verify()
        return self.connection_manager.current_connection.rollback()
