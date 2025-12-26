from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generic, List, Self, TypeVar
from uuid import UUID

from hexagonal.domain import (
    AggregateRoot,
    CloudMessage,
    TIdEntity,
    TQuery,
    TView,
)

from .infrastructure import IBaseInfrastructure

TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any, Any])


class IConnectionManager(IBaseInfrastructure, ABC):
    @contextmanager
    @abstractmethod
    def start_connection(self) -> Any: ...


TManager = TypeVar("TManager", bound=IConnectionManager)


class IBaseRepository(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def connection_manager(self) -> TManager: ...

    @abstractmethod
    def attach_to_unit_of_work(self, uow: "IUnitOfWork[TManager]") -> None: ...

    @abstractmethod
    def detach_from_unit_of_work(self) -> None: ...


class IUnitOfWork(IBaseInfrastructure, ABC, Generic[TManager]):
    @property
    @abstractmethod
    def connection_manager(self) -> TManager: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def attach_repo(self, repo: IBaseRepository[TManager]) -> None: ...

    @abstractmethod
    def detach_repo(self, repo: IBaseRepository[TManager]) -> None: ...

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        if exc_type is None:
            self.commit()
        else:
            self.rollback()


class IAggregateRepository(
    IBaseRepository[TManager],
    Generic[TManager, TAggregate, TIdEntity],
):
    @abstractmethod
    def save(self, aggregate: TAggregate) -> None:
        """Persistir el agregado en el almacenamiento."""
        ...

    @abstractmethod
    def get(self, id: TIdEntity) -> TAggregate:
        """Recuperar el agregado por su ID."""
        ...

    @abstractmethod
    def delete(self, id: TIdEntity) -> TAggregate:
        """Eliminar el agregado por su ID."""
        ...


class IOutboxRepository(IBaseRepository[TManager]):
    """Puerto para manejar eventos pendientes de publicar (write-side)."""

    @abstractmethod
    def save(self, *message: CloudMessage[Any]) -> None:
        """Guardar evento en la tabla Outbox en la misma transacción del agregado."""
        ...

    @abstractmethod
    def fetch_pending(self, limit: int | None = None) -> list[CloudMessage[Any]]:
        """Recuperar eventos no publicados aún."""
        ...

    @abstractmethod
    def mark_as_published(self, *message_ids: UUID) -> None:
        """Marcar un evento como publicado correctamente."""
        ...

    @abstractmethod
    def mark_as_failed(self, *message_ids: UUID, error: str) -> None:
        """Incrementar intentos o marcar el evento como fallido."""
        ...


class IInboxRepository(IBaseRepository[TManager]):
    """Puerto para procesar mensajes de entrada de forma idempotente."""

    @abstractmethod
    def register_message(
        self,
        message: CloudMessage[Any],
        handler: str,
        max_retries: int = 3,
    ) -> bool:
        """
        Intenta registrar un mensaje.
        Retorna False si ya existe (duplicado).
        """
        ...

    @abstractmethod
    def mark_as_processed(self, message_id: UUID, handler: str) -> None:
        """Marcar el mensaje como procesado exitosamente."""
        ...

    @abstractmethod
    def mark_as_failed(self, message_id: UUID, handler: str, error: str) -> None:
        """Marcar el mensaje como fallido."""
        ...


class ISearchRepository(IBaseRepository[TManager], Generic[TManager, TQuery, TView]):
    @abstractmethod
    def search(self, query: TQuery) -> List[TView]:
        """Buscar objetos de valor según el query proporcionado."""
        ...


class IPairInboxOutbox(IBaseInfrastructure, Generic[TManager]):
    @property
    @abstractmethod
    def inbox(self) -> IInboxRepository[TManager]: ...

    @property
    @abstractmethod
    def outbox(self) -> IOutboxRepository[TManager]: ...
