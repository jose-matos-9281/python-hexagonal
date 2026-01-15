"""SQLAlchemy repository adapter for event-sourced aggregates."""

from __future__ import annotations

import logging
from typing import Any, ClassVar, Dict, Mapping, Sequence, Tuple, TypeVar, cast
from uuid import UUID

from eventsourcing.domain import CanMutateAggregate
from eventsourcing.persistence import StoredEvent
from eventsourcing.utils import strtobool
from sqlalchemy import Connection, delete, insert, select, update

from hexagonal.adapters.drivens.repository.base import BaseAggregateRepositoryAdapter
from hexagonal.domain import (
    AggregateNotFound,
    AggregateRoot,
    AggregateSnapshot,
    AggregateVersionMismatch,
    SnapshotState,
    TIdEntity,
)

from .datastore import SQLAlchemyConnectionContextManager
from .models import create_aggregates_table, create_events_table

TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any, Any])

logger = logging.getLogger(__name__)


class SQLAlchemyRepositoryAdapter(
    BaseAggregateRepositoryAdapter[
        SQLAlchemyConnectionContextManager, TAggregate, TIdEntity
    ]
):
    """SQLAlchemy repository adapter for event-sourced aggregates.

    This adapter implements the IAggregateRepository interface using SQLAlchemy
    as the backing store. It handles the persistence and retrieval of event-sourced
    aggregates, including snapshotting and event history.

    Supports multiple database backends (PostgreSQL, MySQL, SQLite) through
    SQLAlchemy's abstraction layer.

    Args:
        mapper: Mapper for converting between domain and persistence models
        connection_manager: SQLAlchemy connection context manager
    """

    ENV: ClassVar[Dict[str, str]] = {
        "TABLE_NAME": "aggregates",
        "CREATE_TABLES": "False",
    }

    def initialize(self, env: Mapping[str, str]) -> None:
        """Initialize the repository from environment variables.

        Args:
            env: Environment variables mapping

        Environment variables:
            TABLE_NAME: Base name for the database tables (default: aggregates)
            SCHEMA_NAME: Database schema name (optional)
            CREATE_TABLES: If True, create tables on initialization (default: False)
        """
        super().initialize(env)
        self._table_name: str = self.env.get("TABLE_NAME", "aggregates")
        self._schema_name: str | None = self.env.get("SCHEMA_NAME")
        create_tables = strtobool(self.env.get("CREATE_TABLES", "False"))

        # Create table objects
        self._aggregates_table = create_aggregates_table(
            self._table_name, self._schema_name
        )
        self._events_table = create_events_table(self._table_name, self._schema_name)

        if create_tables:
            self.create_tables()

    def create_tables(self) -> None:
        """Create the required database tables if they don't exist."""
        engine = self.connection_manager.datastore.engine
        # Create only this repository's tables
        self._aggregates_table.create(engine, checkfirst=True)
        self._events_table.create(engine, checkfirst=True)
        logger.debug(
            "Tables created: %s, %s",
            self._aggregates_table.name,
            self._events_table.name,
        )

    def _get_table_name(self) -> str:
        """Get the full aggregate snapshots table name."""
        return f"aggregates_{self._table_name}"

    def _get_event_history_table_name(self) -> str:
        """Get the full event history table name."""
        return f"aggregates_{self._table_name}_events"

    def _verify_new_aggregate(
        self, conn: Connection, aggregate: TAggregate
    ) -> Tuple[Sequence[CanMutateAggregate[UUID]], bool]:
        """Verify aggregate version and collect pending events.

        Args:
            conn: SQLAlchemy connection
            aggregate: The aggregate to verify

        Returns:
            Tuple of (pending events, is_new flag)

        Raises:
            AggregateVersionMismatch: If aggregate version doesn't match stored version
        """
        actual_agg = self._get_aggregate(conn, aggregate.value_id)
        eventos = aggregate.collect_events()
        if actual_agg is None:
            return eventos, True
        if actual_agg.originator_version != aggregate.version - len(eventos):
            raise AggregateVersionMismatch(
                f"Aggregate {self.aggregate_name} with id {aggregate.value_id}"
                " has a different version"
            )
        return eventos, False

    def _insert_snapshot(
        self, conn: Connection, snap: AggregateSnapshot[SnapshotState[TIdEntity]]
    ) -> None:
        """Insert a new aggregate snapshot.

        Args:
            conn: SQLAlchemy connection
            snap: The aggregate snapshot to insert
        """
        stored_event = self._mapper.to_stored_event(snap)
        stmt = insert(self._aggregates_table).values(
            originator_id=str(stored_event.originator_id),
            aggregate_name=self.aggregate_name,
            originator_version=stored_event.originator_version,
            topic=stored_event.topic,
            state=stored_event.state,
            timestamp=snap.timestamp,
        )
        conn.execute(stmt)

    def _update_snapshot(
        self, conn: Connection, snap: AggregateSnapshot[SnapshotState[TIdEntity]]
    ) -> None:
        """Update an existing aggregate snapshot.

        Args:
            conn: SQLAlchemy connection
            snap: The aggregate snapshot with updated data
        """
        stored_event = self._mapper.to_stored_event(snap)
        originator_id = str(stored_event.originator_id)
        stmt = (
            update(self._aggregates_table)
            .where(
                self._aggregates_table.c.originator_id == originator_id,
                self._aggregates_table.c.aggregate_name == self.aggregate_name,
            )
            .values(
                originator_version=stored_event.originator_version,
                topic=stored_event.topic,
                state=stored_event.state,
                timestamp=snap.timestamp,
            )
        )
        conn.execute(stmt)

    def _save_event_history(
        self, conn: Connection, events: Sequence[CanMutateAggregate[UUID]]
    ) -> None:
        """Save events to the event history table.

        Args:
            conn: SQLAlchemy connection
            events: Sequence of domain events to persist
        """
        if not events:
            return

        stored_events: list[dict[str, Any]] = []
        for event in events:
            stored: StoredEvent = self._mapper.to_stored_event(event)
            stored_events.append(
                {
                    "originator_id": str(stored.originator_id),
                    "aggregate_name": self.aggregate_name,
                    "originator_version": stored.originator_version,
                    "topic": stored.topic,
                    "state": stored.state,
                    "timestamp": event.timestamp,
                }
            )
        stmt = insert(self._events_table)
        conn.execute(stmt, stored_events)

    def save(self, aggregate: TAggregate) -> None:
        """Save an aggregate to the repository.

        Persists the aggregate snapshot and all pending events to the database.
        Uses optimistic locking via version checking.

        Args:
            aggregate: The aggregate to save

        Raises:
            AggregateVersionMismatch: If concurrent modification detected
            RuntimeError: If not attached to a unit of work
        """
        self.verify()
        with self.connection_manager.cursor() as conn:
            eventos, new = self._verify_new_aggregate(conn, aggregate)
            snapshot = aggregate.take_snapshot()
            if new:
                self._insert_snapshot(conn, snapshot)
            else:
                self._update_snapshot(conn, snapshot)
            self._save_event_history(conn, eventos)
            # Verify save was successful
            agg = self._get_aggregate(conn, aggregate.value_id)
            assert agg is not None

    def _get_aggregate(self, conn: Connection, id: TIdEntity) -> StoredEvent | None:
        """Fetch aggregate snapshot from database.

        Args:
            conn: SQLAlchemy connection
            id: The aggregate ID to fetch

        Returns:
            StoredEvent if found, None otherwise
        """
        stmt = (
            select(
                self._aggregates_table.c.originator_id,
                self._aggregates_table.c.originator_version,
                self._aggregates_table.c.topic,
                self._aggregates_table.c.state,
            )
            .where(
                self._aggregates_table.c.originator_id == str(id.value),
                self._aggregates_table.c.aggregate_name == self.aggregate_name,
            )
            .limit(1)
        )

        result = conn.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return StoredEvent(
            originator_id=row.originator_id,
            originator_version=row.originator_version,
            topic=row.topic,
            state=row.state,
        )

    def get(self, id: TIdEntity) -> TAggregate:
        """Get an aggregate by its ID.

        Args:
            id: The aggregate ID to retrieve

        Returns:
            The reconstructed aggregate

        Raises:
            AggregateNotFound: If no aggregate exists with the given ID
            RuntimeError: If not attached to a unit of work
        """
        self.verify()
        with self.connection_manager.cursor() as conn:
            stored_event = self._get_aggregate(conn, id)
        if stored_event is None:
            raise AggregateNotFound(
                f"Aggregate {self.aggregate_name} with id {id} not found"
            )
        snap_event = self._mapper.to_domain_event(stored_event)
        assert isinstance(snap_event, self._type_of_aggregate.Snapshot)
        return cast(TAggregate, snap_event.mutate(None))

    def _delete(self, conn: Connection, id: TIdEntity) -> None:
        """Delete aggregate snapshot from database.

        Args:
            conn: SQLAlchemy connection
            id: The aggregate ID to delete
        """
        stmt = delete(self._aggregates_table).where(
            self._aggregates_table.c.originator_id == str(id.value),
            self._aggregates_table.c.aggregate_name == self.aggregate_name,
        )
        conn.execute(stmt)

    def delete(self, id: TIdEntity) -> TAggregate:
        """Delete an aggregate from the repository.

        Triggers a Deleted event, saves it to history, and removes the snapshot.

        Args:
            id: The aggregate ID to delete

        Returns:
            The deleted aggregate (with Deleted event applied)

        Raises:
            AggregateNotFound: If no aggregate exists with the given ID
            RuntimeError: If not attached to a unit of work
        """
        self.verify()
        agg = self.get(id)

        agg.trigger_event(event_class=agg.Deleted)
        events = agg.collect_events()
        with self.connection_manager.cursor() as conn:
            self._save_event_history(conn, events)
            self._delete(conn, id)
        return agg
